import io
from typing import List, Dict, Any
from PIL import Image

from ai.models.vision.infer import infer_pil


def infer(images: List[bytes]) -> Dict[str, Any]:
    if not images:
        return {"findings": [], "meta": {}, "qc": {"status": "fail", "reasons": ["no_images"]}}

    # 현재는 첫 장만 사용(원하면 여러 장 loop 가능)
    pil = Image.open(io.BytesIO(images[0]))
    return infer_pil(pil)