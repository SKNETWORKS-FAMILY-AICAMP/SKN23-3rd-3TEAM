"""
Deep Model Inference Script
============================
정밀 분석 모드 - 정면(F) + 좌(L) + 우(R) 3장으로 피부 정밀 분석

입력: 정면/좌/우 이미지 경로 (jpg/png)
출력: 피부 정밀 분석 결과 dict

사용 예시:
    from deep_inference import predict_deep
    result = predict_deep(
        img_F="/path/to/front.jpg",
        img_L="/path/to/left.jpg",
        img_R="/path/to/right.jpg"
    )
"""

import os
import cv2
import json
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
    from ai.config.settings import SKIN_AI_DEEP_CHECKPOINT as CHECKPOINT_DIR
except ImportError:
    CHECKPOINT_DIR = _os.getenv("SKIN_AI_CHECKPOINT_DIR", "skin_ai/checkpoint") + "/deep"
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 256

# ── Area별 출력 항목 정의 ──────────────────────────────
AREA_REGRESSION = {
    "0": ["pigmentation_count"],
    "1": ["forehead_moisture", "forehead_elasticity_R2"],
    "2": [],
    "3": ["l_perocular_wrinkle_Ra"],
    "4": ["r_perocular_wrinkle_Ra"],
    "5": ["l_cheek_moisture", "l_cheek_elasticity_R2", "l_cheek_pore"],
    "6": ["r_cheek_moisture", "r_cheek_elasticity_R2", "r_cheek_pore"],
    "8": ["chin_moisture", "chin_elasticity_R2"],
}
AREA_CLASS_NUM = {
    "1": {"forehead_wrinkle": 7, "forehead_pigmentation": 6},
    "2": {"glabellus_wrinkle": 7},
    "3": {"l_perocular_wrinkle": 7},
    "4": {"r_perocular_wrinkle": 7},
    "5": {"l_cheek_pore": 6, "l_cheek_pigmentation": 6},
    "6": {"r_cheek_pore": 6, "r_cheek_pigmentation": 6},
    "8": {"chin_wrinkle": 7},
}
AREA_REG_OUT = {"0":1, "1":2, "2":0, "3":1, "4":1, "5":3, "6":3, "8":2}
AREA_CLS_OUT = {"0":0, "1":13, "2":7, "3":7, "4":7, "5":12, "6":12, "8":7}

# ── 역정규화 ───────────────────────────────────────────
def _denormalize(key: str, value: float) -> float:
    if "moisture" in key:   return round(value * 100.0, 1)
    if key.endswith("_R2"): return round(value, 3)
    if key.endswith("_Ra"): return round(value * 50.0,  1)
    if "pore"  in key:      return round(value * 2600.0, 1)
    if "count" in key:      return round(value * 350.0,  1)
    return round(value, 3)

# ── 신뢰도 등급 ────────────────────────────────────────
# LLM이 각 항목의 신뢰도를 참고하여 응답 생성 시 활용
RELIABILITY = {
    # 🏆 높음 (MAE < 0.05)
    "forehead_elasticity_R2":  "high",
    "l_cheek_pore":            "high",
    "r_cheek_pore":            "high",

    # ✅ 보통 (MAE 0.05~0.10)
    "forehead_moisture":       "medium",
    "l_cheek_elasticity_R2":   "medium",
    "l_cheek_moisture":        "medium",
    "r_cheek_elasticity_R2":   "medium",
    "r_perocular_wrinkle_Ra":  "medium",

    # ⚠️ 참고용 (MAE 0.10~0.15)
    "pigmentation_count":      "low",
    "r_cheek_moisture":        "low",

    # ❌ 낮음 (MAE > 0.15) - LLM이 Ra 수치로 대신 해석 권장
    "chin_moisture":           "very_low",
    "chin_elasticity_R2":      "very_low",
    "l_perocular_wrinkle_Ra":  "very_low",
}

# ── 이미지 전처리 ──────────────────────────────────────
TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

def _load_image(img_path: str) -> torch.Tensor:
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"이미지를 불러올 수 없어요: {img_path}")
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return TRANSFORM(Image.fromarray(img_rgb)).unsqueeze(0).to(DEVICE)


# ── 모델 정의 ──────────────────────────────────────────
class AttentionFusion(nn.Module):
    def __init__(self, feat_dim=2048):
        super().__init__()
        self.attn = nn.Sequential(
            nn.Linear(feat_dim * 3, 3),
            nn.Softmax(dim=1)
        )
        self.proj = nn.Sequential(
            nn.Linear(feat_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.4)
        )

    def forward(self, f_F, f_L, f_R):
        w = self.attn(torch.cat([f_F, f_L, f_R], dim=1))
        fused = w[:, 0:1] * f_F + w[:, 1:2] * f_L + w[:, 2:3] * f_R
        return self.proj(fused)


class DeepAreaModel(nn.Module):
    def __init__(self, reg_out: int, cls_out: int):
        super().__init__()
        bb = models.resnet50(weights=ResNet50_Weights.DEFAULT)
        backbone = nn.Sequential(*list(bb.children())[:-1], nn.Flatten())

        self.enc_reg  = backbone                     if reg_out > 0 else None
        self.enc_cls  = backbone                     if cls_out > 0 else None
        self.fusion   = AttentionFusion(2048)        if cls_out > 0 else None
        self.reg_head = nn.Sequential(
            nn.Linear(2048, 512), nn.BatchNorm1d(512), nn.ReLU(), nn.Dropout(0.4),
            nn.Linear(512, 256),  nn.ReLU(),            nn.Dropout(0.4),
            nn.Linear(256, reg_out)
        ) if reg_out > 0 else None
        self.cls_head = nn.Sequential(
            nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.4),
            nn.Linear(256, cls_out)
        ) if cls_out > 0 else None

    def forward(self, x_F, x_L, x_R):
        reg = self.reg_head(self.enc_reg(x_F)) if self.reg_head else None
        cls = None
        if self.cls_head:
            fused = self.fusion(
                self.enc_cls(x_F),
                self.enc_cls(x_L),
                self.enc_cls(x_R)
            )
            cls = self.cls_head(fused)
        return reg, cls


# ── 모델 캐시 ──────────────────────────────────────────
_model_cache: dict = {}

def _get_model(area_id: str) -> DeepAreaModel | None:
    if area_id in _model_cache:
        return _model_cache[area_id]

    ckpt_path = os.path.join(CHECKPOINT_DIR, area_id, "state_dict.bin")
    if not os.path.exists(ckpt_path):
        print(f"[DeepModel] 체크포인트 없음 (area {area_id}): {ckpt_path}", flush=True)
        return None
    print(f"[DeepModel] area {area_id} 로드 완료", flush=True)

    reg_out = AREA_REG_OUT[area_id]
    cls_out = AREA_CLS_OUT[area_id]
    model = DeepAreaModel(reg_out, cls_out).to(DEVICE)

    ckpt = torch.load(ckpt_path, map_location=DEVICE)
    model.load_state_dict(ckpt["model_state"], strict=False)
    model.eval()
    _model_cache[area_id] = model
    return model


# ── 메인 추론 함수 ─────────────────────────────────────
def predict_deep(img_F: str, img_L: str, img_R: str) -> dict:
    """
    정밀 분석: 정면(F) + 좌(L) + 우(R) 3장으로 피부 정밀 분석

    Args:
        img_F: 정면 이미지 경로
        img_L: 좌측 이미지 경로
        img_R: 우측 이미지 경로

    Returns:
        {
            "mode": "deep",
            "measurements": {
                # 수분 (0~100, 높을수록 수분 충분)
                "forehead_moisture": 65.2,
                "l_cheek_moisture": 70.1,
                "r_cheek_moisture": 68.5,
                "chin_moisture": 55.3,       # 신뢰도 낮음

                # 탄력 (0~1, 높을수록 탄력 좋음)
                "forehead_elasticity_R2": 0.621,
                "l_cheek_elasticity_R2": 0.587,
                "r_cheek_elasticity_R2": 0.563,
                "chin_elasticity_R2": 0.410,  # 신뢰도 낮음

                # 주름 Ra (낮을수록 주름 적음)
                "l_perocular_wrinkle_Ra": 18.5,
                "r_perocular_wrinkle_Ra": 20.1,

                # 색소침착
                "pigmentation_count": 95.0,

                # 모공 (0~2600, 낮을수록 모공 작음)
                "l_cheek_pore": 2.0,
                "r_cheek_pore": 2.0,
            },
            "grades": {
                # 등급 (0~6, 낮을수록 양호)
                # ⚠️ 참고용 - Ra 수치와 함께 해석 권장
                "forehead_wrinkle": 1,
                "glabellus_wrinkle": 2,
                "l_perocular_wrinkle": 3,
                "r_perocular_wrinkle": 3,
                "l_cheek_pore": 2,
                "r_cheek_pore": 2,
                "l_cheek_pigmentation": 2,
                "r_cheek_pigmentation": 3,
                "chin_wrinkle": 1,
                "forehead_pigmentation": 1,
            },
            "reliability": {
                # 각 항목 신뢰도: "high" | "medium" | "low" | "very_low"
                "forehead_moisture": "medium",
                ...
            }
        }
    """
    F = _load_image(img_F)
    L = _load_image(img_L)
    R = _load_image(img_R)

    measurements = {}
    grades = {}

    for area_id in ["0", "1", "2", "3", "4", "5", "6", "8"]:
        model = _get_model(area_id)
        if model is None:
            continue

        with torch.no_grad():
            reg_pred, cls_pred = model(F, L, R)

        # Regression
        reg_keys = AREA_REGRESSION.get(area_id, [])
        if reg_pred is not None:
            for i, key in enumerate(reg_keys):
                measurements[key] = _denormalize(key, reg_pred[0][i].item())

        # Classification
        cls_info = AREA_CLASS_NUM.get(area_id, {})
        if cls_pred is not None:
            offset = 0
            for key, n_out in cls_info.items():
                grades[key] = int(cls_pred[0, offset:offset + n_out].argmax().item())
                offset += n_out

    # 신뢰도 정보 추가
    reliability = {
        key: RELIABILITY.get(key, "medium")
        for key in list(measurements.keys())
    }

    return {
        "mode": "deep",
        "measurements": measurements,
        "grades": grades,
        "reliability": reliability,
    }


# ── 직접 실행 테스트 ───────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("사용법: python deep_inference.py <F이미지> <L이미지> <R이미지>")
        sys.exit(1)

    result = predict_deep(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result, ensure_ascii=False, indent=2))
