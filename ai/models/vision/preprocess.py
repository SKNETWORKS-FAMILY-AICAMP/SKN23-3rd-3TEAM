from PIL import Image
import torchvision.transforms as T
import torch


_TFM = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]),
])


def preprocess_image(pil: Image.Image) -> torch.Tensor:
    if pil.mode != "RGB":
        pil = pil.convert("RGB")
    return _TFM(pil)