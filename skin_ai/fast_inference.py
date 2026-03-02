"""
fast_inference.py
==================
빠른 분석 모드 - 정면 사진 1장으로 피부 5개 항목 분석

입력: 정면 이미지 경로 (jpg/png)
출력:
    {
        "mode": "fast",
        "image": "0001_03_F.jpg",
        "skin_metrics": {
            "moisture":     { "value": 0.6520, "grade": 4 },
            "elasticity":   { "value": 0.6210, "grade": 4 },
            "wrinkle":      { "value": 0.3820, "grade": 2 },
            "pore":         { "value": 0.2100, "grade": 2 },
            "pigmentation": { "value": 0.2720, "grade": 2 }
        }
    }

학습 구조 (노트북 fast_model_multigpu 기준):
    - area 0~8별 ResNet50 기반 모델 (deep과 동일 구조)
    - 정면 1장을 각 area 모델에 통째로 입력
    - METRIC_MAPPING으로 area별 출력 → 5개 항목으로 집계
    - grade: value × 5 → 1~5등급
"""

import os
import json
import cv2
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
from torchvision import transforms, models
from torchvision.models import ResNet50_Weights

# ── 경로 설정 ──────────────────────────────────────────
import sys as _sys, os as _os
_settings_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")
if _settings_path not in _sys.path:
    _sys.path.insert(0, _settings_path)
try:
    from ai.config.settings import SKIN_AI_FAST_CHECKPOINT as CHECKPOINT_DIR
except ImportError:
    CHECKPOINT_DIR = _os.getenv("SKIN_AI_CHECKPOINT_DIR", "skin_ai/checkpoint") + "/fast"

DEVICE   = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 128

# ── Area별 출력 항목 정의 (노트북과 동일) ──────────────
AREA_REG_OUT = {"0":1, "1":2, "2":0, "3":1, "4":1, "5":3, "6":3, "8":2}
AREA_CLS_OUT = {"0":0, "1":13, "2":7, "3":7, "4":7, "5":12, "6":12, "8":7}

# 5개 항목 → area별 regression 출력 인덱스 매핑
METRIC_MAPPING = {
    "moisture"    : [("1", 0), ("5", 0), ("6", 0), ("8", 0)],
    "elasticity"  : [("1", 1), ("5", 1), ("6", 1), ("8", 1)],
    "wrinkle"     : [("3", 0), ("4", 0)],
    "pore"        : [("5", 2), ("6", 2)],
    "pigmentation": [("0", 0)],
}

# ── 정규화 ─────────────────────────────────────────────
TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


# ── 모델 정의 (deep과 동일 구조) ───────────────────────
class FastAreaModel(nn.Module):
    def __init__(self, reg_out: int, cls_out: int):
        super().__init__()
        bb = models.resnet50(weights=ResNet50_Weights.DEFAULT)
        in_features = bb.fc.in_features
        bb.fc = nn.Identity()
        self.backbone = bb
        self.reg_head = nn.Linear(in_features, reg_out) if reg_out > 0 else None
        self.cls_head = nn.Linear(in_features, cls_out) if cls_out > 0 else None

    def forward(self, x):
        feat = self.backbone(x)
        reg = torch.sigmoid(self.reg_head(feat)) if self.reg_head else None
        cls = self.cls_head(feat) if self.cls_head else None
        return reg, cls


# ── 모델 로딩 캐시 ─────────────────────────────────────
_model_cache: dict = {}

def _get_model(area_id: str) -> FastAreaModel | None:
    if area_id in _model_cache:
        return _model_cache[area_id]

    ckpt_path = os.path.join(CHECKPOINT_DIR, area_id, "state_dict.bin")
    if not os.path.exists(ckpt_path):
        print(f"[FastModel] 체크포인트 없음 (area {area_id}): {ckpt_path}", flush=True)
        return None

    reg_out = AREA_REG_OUT.get(area_id, 0)
    cls_out = AREA_CLS_OUT.get(area_id, 0)
    if reg_out == 0 and cls_out == 0:
        return None

    model = FastAreaModel(reg_out, cls_out).to(DEVICE)
    ckpt  = torch.load(ckpt_path, map_location=DEVICE)
    model.load_state_dict(ckpt["model_state"], strict=False)
    model.eval()
    _model_cache[area_id] = model
    print(f"[FastModel] area {area_id} 로드 완료", flush=True)
    return model


# ── grade 변환 (value 0~1 → 1~5등급) ──────────────────
def _value_to_grade(value: float, n_grades: int = 5) -> int:
    if np.isnan(value):
        return None
    return min(int(value * n_grades) + 1, n_grades)


# ── 이미지 로딩 ────────────────────────────────────────
def _load_image(img_path: str) -> torch.Tensor:
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"이미지를 불러올 수 없어요: {img_path}")
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    tensor  = TRANSFORM(Image.fromarray(img_rgb))
    return tensor.unsqueeze(0).to(DEVICE)


# ── 메인 추론 함수 ─────────────────────────────────────
def predict_fast(img_path: str) -> dict:
    """
    빠른 분석: 정면 사진 1장 → 피부 5개 항목 수치 + 등급

    Args:
        img_path: 정면 이미지 경로 (str 또는 bytes)

    Returns:
        {
            "mode": "fast",
            "image": "파일명",
            "skin_metrics": {
                "moisture":     { "value": 0.652, "grade": 4 },
                "elasticity":   { "value": 0.621, "grade": 4 },
                "wrinkle":      { "value": 0.382, "grade": 2 },
                "pore":         { "value": 0.210, "grade": 2 },
                "pigmentation": { "value": 0.272, "grade": 2 }
            }
        }
    """
    # bytes 입력 지원 (vision_node에서 tmpfile 경로로 전달하므로 str 기준)
    img_tensor = _load_image(img_path)
    img_name   = os.path.basename(img_path)

    # area별 추론
    area_preds: dict = {}
    for area_id in AREA_REG_OUT:
        if AREA_REG_OUT[area_id] == 0:
            continue
        model = _get_model(area_id)
        if model is None:
            continue
        with torch.no_grad():
            reg_pred, _ = model(img_tensor)
        if reg_pred is not None:
            area_preds[area_id] = reg_pred.cpu().numpy()[0]

    # 5개 항목으로 집계 (area별 평균)
    skin_metrics: dict = {}
    for metric, area_idx_list in METRIC_MAPPING.items():
        vals = [
            float(area_preds[a][i])
            for a, i in area_idx_list
            if a in area_preds and i < len(area_preds[a])
        ]
        if vals:
            avg = float(np.mean(vals))
            skin_metrics[metric] = {
                "value": round(avg, 4),
                "grade": _value_to_grade(avg),
            }

    return {
        "mode"        : "fast",
        "image"       : img_name,
        "skin_metrics": skin_metrics,
    }


# ── 직접 실행 테스트 ───────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("사용법: python fast_inference.py <이미지경로>")
        sys.exit(1)
    result = predict_fast(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
