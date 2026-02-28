# ai/models/vision/face_detector.py
import os
import urllib.request
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image

# ✅ OpenCV DNN face detector (ResNet-10 SSD)
# prototxt는 opencv repo에 있고, caffemodel(fp16)은 opencv_3rdparty의 "20180205_fp16" 쪽이 현재 많이 쓰임. :contentReference[oaicite:1]{index=1}

_PROTO_URLS = [
    # opencv master
    "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
]

_MODEL_URLS = [
    # ✅ (중요) fp16 모델: 20180205_fp16 경로 (이게 404 문제 해결 포인트) :contentReference[oaicite:2]{index=2}
    "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel",
    # 혹시 fp16이 막히면 fp32 모델(다른 레포 미러)도 fallback으로 시도
    "https://raw.githubusercontent.com/sr6033/face-detection-with-OpenCV-and-DNN/master/res10_300x300_ssd_iter_140000.caffemodel",
]

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CACHE_DIR = os.path.join(_THIS_DIR, "_models")
os.makedirs(_CACHE_DIR, exist_ok=True)

_PROTO_PATH = os.path.join(_CACHE_DIR, "deploy.prototxt")
_MODEL_PATH = os.path.join(_CACHE_DIR, "res10_300x300_ssd_iter_140000_fp16.caffemodel")

_NET = None  # lazy load


def _download_one(url: str, dst: str):
    urllib.request.urlretrieve(url, dst)


def _download_if_needed():
    if not os.path.exists(_PROTO_PATH):
        last_err = None
        for url in _PROTO_URLS:
            try:
                _download_one(url, _PROTO_PATH)
                last_err = None
                break
            except Exception as e:
                last_err = e
        if last_err is not None:
            raise RuntimeError(f"Failed to download prototxt. last_error={last_err}")

    if not os.path.exists(_MODEL_PATH):
        last_err = None
        for url in _MODEL_URLS:
            try:
                _download_one(url, _MODEL_PATH)
                last_err = None
                break
            except Exception as e:
                last_err = e
        if last_err is not None:
            raise RuntimeError(f"Failed to download caffemodel. last_error={last_err}")


def _get_net():
    global _NET
    if _NET is not None:
        return _NET
    _download_if_needed()
    _NET = cv2.dnn.readNetFromCaffe(_PROTO_PATH, _MODEL_PATH)
    return _NET


# bbox: (x1, y1, x2, y2) pixel coords
def detect_faces(pil: Image.Image, min_conf: float = 0.6) -> List[Tuple[int, int, int, int]]:
    if pil.mode != "RGB":
        pil = pil.convert("RGB")

    img = np.array(pil)  # RGB
    h, w = img.shape[:2]
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    net = _get_net()
    blob = cv2.dnn.blobFromImage(
        bgr, 1.0, (300, 300),
        (104.0, 177.0, 123.0),
        swapRB=False, crop=False
    )
    net.setInput(blob)
    dets = net.forward()  # (1,1,N,7)

    boxes: List[Tuple[int, int, int, int]] = []
    for i in range(dets.shape[2]):
        conf = float(dets[0, 0, i, 2])
        if conf < min_conf:
            continue
        x1 = int(dets[0, 0, i, 3] * w)
        y1 = int(dets[0, 0, i, 4] * h)
        x2 = int(dets[0, 0, i, 5] * w)
        y2 = int(dets[0, 0, i, 6] * h)

        x1 = max(0, min(w - 1, x1))
        y1 = max(0, min(h - 1, y1))
        x2 = max(0, min(w, x2))
        y2 = max(0, min(h, y2))

        if x2 > x1 and y2 > y1:
            boxes.append((x1, y1, x2, y2))

    return boxes