# ai/models/vision/infer.py
import os
from typing import Dict, Any, Optional, Tuple, List

import torch
import numpy as np
from PIL import Image

from ai.models.vision.model import MultiTaskCNN
from ai.models.vision.preprocess import preprocess_image
from ai.models.vision.face_detector import detect_faces


_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_MODEL: Optional[torch.nn.Module] = None
_META: Optional[Dict[str, Any]] = None


def _load_ckpt() -> Dict[str, Any]:
    path = os.environ.get("VISION_MODEL_PATH", "ai/assets/models/best.pt")
    ckpt = torch.load(path, map_location=_DEVICE)
    if not isinstance(ckpt, dict) or "model_state" not in ckpt:
        raise RuntimeError(
            f"Unexpected checkpoint format. type={type(ckpt)} "
            f"keys={list(ckpt.keys()) if isinstance(ckpt, dict) else None}"
        )
    return ckpt


def _get_model_and_meta():
    global _MODEL, _META
    if _MODEL is not None and _META is not None:
        return _MODEL, _META

    ckpt = _load_ckpt()

    reg_cols = ckpt.get("reg_cols", [])
    cls_cols = ckpt.get("cls_cols", [])
    cls_label_maps = ckpt.get("cls_label_maps", {})  # {col: {label_str: idx}}

    # cls head별 클래스 개수
    cls_num_classes = {}
    for c in cls_cols:
        lm = cls_label_maps.get(c, {})
        cls_num_classes[c] = len(lm)

    model = MultiTaskCNN(
        backbone_name="resnet18",
        reg_out=len(reg_cols),
        cls_num_classes=cls_num_classes,
        pretrained=False,
    ).to(_DEVICE)

    model.load_state_dict(ckpt["model_state"], strict=True)
    model.eval()

    # idx -> label
    cls_id_to_label = {}
    for c in cls_cols:
        lm = cls_label_maps.get(c, {})
        inv = {}
        for label_str, idx in lm.items():
            try:
                inv[int(idx)] = str(label_str)
            except Exception:
                continue
        cls_id_to_label[c] = inv

    _MODEL = model
    _META = {
        "device": str(_DEVICE),
        "model_path": os.environ.get("VISION_MODEL_PATH", "ai/assets/models/best.pt"),
        "reg_cols": reg_cols,
        "cls_cols": cls_cols,
        "cls_label_maps": cls_label_maps,
        "cls_id_to_label": cls_id_to_label,
    }
    return _MODEL, _META


def _region_from_col(col: str) -> str:
    """
    reg_cols / cls_cols 이름에서 region 대충 추출.
    예: reg_l_cheek_pore -> l_cheek
        cls_chin_sagging  -> chin
    """
    s = col.lower().replace("reg_", "").replace("cls_", "")
    parts = s.split("_")
    if len(parts) >= 2 and parts[0] in {"l", "r"}:
        return f"{parts[0]}_{parts[1]}"
    return parts[0] if parts else "global"


def _softmax_np(logits: np.ndarray) -> np.ndarray:
    logits = logits - np.max(logits)
    exp = np.exp(logits)
    return exp / (np.sum(exp) + 1e-12)


def _pick_largest_box(boxes: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
    def area(b):
        x1, y1, x2, y2 = b
        return max(0, x2 - x1) * max(0, y2 - y1)
    return sorted(boxes, key=area, reverse=True)[0]


def _expand_box(
    box: Tuple[int, int, int, int],
    img_w: int,
    img_h: int,
    scale: float = 1.5
) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    bw = (x2 - x1)
    bh = (y2 - y1)

    nw = bw * scale
    nh = bh * scale

    nx1 = int(max(0, cx - nw / 2))
    ny1 = int(max(0, cy - nh / 2))
    nx2 = int(min(img_w, cx + nw / 2))
    ny2 = int(min(img_h, cy + nh / 2))
    return nx1, ny1, nx2, ny2


@torch.inference_mode()
def infer_pil(
    pil: Image.Image,
    face_min_conf: float = 0.6,
    box_expand_scale: float = 1.5,
    cls_conf_threshold: float = 0.6,
    min_face_side: int = 180,
    min_face_area_ratio: float = 0.08,
) -> Dict[str, Any]:
    """
    Returns:
      {
        "findings": [...],
        "meta": meta,
        "qc": {"status": "pass/fail", "reasons": [...]},
        "face_box": {...}
      }
    """
    model, meta = _get_model_and_meta()

    if pil.mode != "RGB":
        pil = pil.convert("RGB")

    img_w, img_h = pil.size

    # 1) 얼굴 검출 (DNN)
    boxes = detect_faces(pil, min_conf=face_min_conf)
    if not boxes:
        return {
            "findings": [],
            "meta": meta,
            "qc": {"status": "fail", "reasons": ["no_face_detected"]},
        }

    # 2) 가장 큰 얼굴 선택 + 박스 확장
    base_box = _pick_largest_box(boxes)
    x1, y1, x2, y2 = _expand_box(base_box, img_w, img_h, scale=box_expand_scale)

    # 3) QC 강화
    reasons = []
    face_w = x2 - x1
    face_h = y2 - y1

    if min(face_w, face_h) < min_face_side:
        reasons.append("face_crop_too_small")

    area_ratio = (face_w * face_h) / (img_w * img_h + 1e-9)
    if area_ratio < min_face_area_ratio:
        reasons.append("face_area_too_small")

    face_box = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

    if reasons:
        return {
            "findings": [],
            "meta": meta,
            "qc": {"status": "fail", "reasons": reasons},
            "face_box": face_box,
        }

    # 4) crop -> preprocess -> infer
    face = pil.crop((x1, y1, x2, y2))
    x = preprocess_image(face).unsqueeze(0).to(_DEVICE)

    reg_t, cls_logits = model(x)  # ✅ tuple output

    findings: List[Dict[str, Any]] = []

    # Regression
    reg_cols = meta.get("reg_cols", [])
    if reg_cols:
        reg_vals = reg_t[0].detach().cpu().numpy().tolist()
        for name, score in zip(reg_cols, reg_vals):
            findings.append({
                "region": _region_from_col(name),
                "name": name,
                "score": float(score),
                "type": "reg",
            })

    # Classification (confidence gate)
    cls_cols = meta.get("cls_cols", [])
    id2label_map = meta.get("cls_id_to_label", {})
    for col in cls_cols:
        if col not in cls_logits:
            continue

        logits = cls_logits[col][0].detach().cpu().numpy()
        probs = _softmax_np(logits)
        pred_id = int(np.argmax(probs))
        conf = float(probs[pred_id])

        if conf < cls_conf_threshold:
            continue

        pred_label = id2label_map.get(col, {}).get(pred_id, str(pred_id))
        findings.append({
            "region": _region_from_col(col),
            "name": f"{col}:{pred_label}",
            "score": conf,
            "type": "cls",
        })

    findings.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    return {
        "findings": findings,
        "meta": meta,
        "qc": {"status": "pass", "reasons": []},
        "face_box": face_box,
        "debug": {
            "n_boxes": len(boxes),
            "base_box": {"x1": base_box[0], "y1": base_box[1], "x2": base_box[2], "y2": base_box[3]},
            "area_ratio": float(area_ratio),
            "box_expand_scale": float(box_expand_scale),
            "cls_conf_threshold": float(cls_conf_threshold),
        }
    }