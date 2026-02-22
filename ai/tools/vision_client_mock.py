# import os
# import io
# from typing import List, Dict, Any, Optional

# import torch
# from PIL import Image

# # ✅ 팀원이 준 모델 정의를 여기에 맞춰 import
# # 예: from app.models.vision.model import SkinNet
# from app.models.vision.model import SkinNet  # <-- 너희 실제 클래스명으로 변경 필요

# # ✅ 전처리(Resize/Normalize 등)도 팀원 규칙에 맞춰 구현/수정
# from app.models.vision.preprocess import preprocess_image  # <-- 아래 예시 제공

# _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# _MODEL: Optional[torch.nn.Module] = None
# _META: Optional[Dict[str, Any]] = None


# def _load_checkpoint() -> Dict[str, Any]:
#     path = os.environ.get("VISION_MODEL_PATH", "app/assets/models/best.pt")
#     ckpt = torch.load(path, map_location="cpu")
#     if not isinstance(ckpt, dict) or "model_state" not in ckpt:
#         raise RuntimeError(f"Unexpected checkpoint format: keys={list(getattr(ckpt, 'keys', lambda: [])())}")
#     return ckpt


# def _get_model_and_meta():
#     global _MODEL, _META
#     if _MODEL is not None and _META is not None:
#         return _MODEL, _META

#     ckpt = _load_checkpoint()

#     reg_cols = ckpt.get("reg_cols", [])
#     cls_cols = ckpt.get("cls_cols", [])
#     cls_label_maps = ckpt.get("cls_label_maps", {})

#     # ✅ 모델 생성: 입력/출력 차원은 팀원 모델 정의에 맞춰야 함
#     # 예시: 회귀 head 개수 = len(reg_cols), 분류 head/클래스 수는 cls_label_maps 기반
#     # 아래는 흔한 패턴 예시이므로, 팀원 코드에 맞춰 수정 필수.
#     model = SkinNet(
#         n_reg=len(reg_cols),
#         cls_cols=cls_cols,
#         cls_label_maps=cls_label_maps,
#     )

#     model.load_state_dict(ckpt["model_state"], strict=True)
#     model.to(_DEVICE)
#     model.eval()

#     _MODEL = model
#     _META = {
#         "reg_cols": reg_cols,
#         "cls_cols": cls_cols,
#         "cls_label_maps": cls_label_maps,
#         "device": str(_DEVICE),
#         "model_path": os.environ.get("VISION_MODEL_PATH", "app/assets/models/best.pt"),
#     }
#     return _MODEL, _META


# def _bytes_to_pil(img_bytes: bytes) -> Image.Image:
#     im = Image.open(io.BytesIO(img_bytes))
#     if im.mode != "RGB":
#         im = im.convert("RGB")
#     return im


# @torch.inference_mode()
# def infer(images: List[bytes]) -> Dict[str, Any]:
#     model, meta = _get_model_and_meta()
#     findings: List[Dict[str, Any]] = []

#     if not images:
#         return {"findings": [], "meta": meta}

#     for idx, b in enumerate(images):
#         pil = _bytes_to_pil(b)

#         # (1) 전처리 -> tensor [1, C, H, W]
#         x = preprocess_image(pil).unsqueeze(0).to(_DEVICE)

#         # (2) 모델 forward
#         # ✅ 모델 반환 형태는 팀원 코드에 따라 다름:
#         # 예: {"reg": tensor, "cls": {"acne": logits, ...}} 같은 형태가 흔함
#         out = model(x)

#         # -----------------------
#         # (3) 회귀 결과 처리
#         # -----------------------
#         # out["reg"]: shape [1, n_reg] 가정
#         if isinstance(out, dict) and "reg" in out and meta["reg_cols"]:
#             reg = out["reg"][0].detach().float().cpu().tolist()
#             for name, score in zip(meta["reg_cols"], reg):
#                 # score 정규화가 필요하면 여기서 처리 (0~1로 clamp 등)
#                 findings.append({
#                     "region": "global",
#                     "name": name,
#                     "score": float(score),
#                     "image_index": idx,
#                     "type": "reg",
#                 })

#         # -----------------------
#         # (4) 분류 결과 처리
#         # -----------------------
#         # out["cls"]가 dict: {col: logits tensor [1, num_class]} 가정
#         if isinstance(out, dict) and "cls" in out and meta["cls_cols"]:
#             cls_out = out["cls"]
#             for col in meta["cls_cols"]:
#                 if col not in cls_out:
#                     continue
#                 logits = cls_out[col][0].detach().float().cpu()
#                 prob = torch.softmax(logits, dim=0)
#                 pred_id = int(torch.argmax(prob).item())
#                 conf = float(prob[pred_id].item())

#                 # label map 적용
#                 label_map = meta["cls_label_maps"].get(col, {})
#                 pred_label = label_map.get(pred_id, str(pred_id))

#                 findings.append({
#                     "region": "global",
#                     "name": f"{col}:{pred_label}",
#                     "score": conf,
#                     "image_index": idx,
#                     "type": "cls",
#                 })

#     # 점수 높은 것 우선
#     findings.sort(key=lambda x: x.get("score", 0.0), reverse=True)
#     return {"findings": findings, "meta": meta}