# model.py
import torch
from torch import nn
import torchvision.models as models


class MultiTaskCNN(nn.Module):
    """
    backbone: resnet18 or efficientnet_b0
    output:
      - reg: (B, reg_out)
      - cls_logits: dict[str, Tensor], each (B, n_classes)
    """
    def __init__(self, backbone_name="resnet18", reg_out=5, cls_num_classes=None, pretrained=True):
        super().__init__()
        cls_num_classes = cls_num_classes or {}

        if backbone_name == "resnet18":
            weights = models.ResNet18_Weights.DEFAULT if pretrained else None
            backbone = models.resnet18(weights=weights)
            num_feats = backbone.fc.in_features
            backbone.fc = nn.Identity()
        elif backbone_name == "efficientnet_b0":
            weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
            backbone = models.efficientnet_b0(weights=weights)
            num_feats = backbone.classifier[1].in_features
            backbone.classifier = nn.Identity()
        else:
            raise ValueError(f"Unsupported backbone: {backbone_name}")

        self.backbone = backbone
        self.reg_head = nn.Sequential(
            nn.Linear(num_feats, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, reg_out)
        )

        self.cls_heads = nn.ModuleDict()
        for k, ncls in cls_num_classes.items():
            self.cls_heads[k] = nn.Sequential(
                nn.Linear(num_feats, 256),
                nn.ReLU(inplace=True),
                nn.Linear(256, ncls)
            )

    def forward(self, x):
        feats = self.backbone(x)
        reg = self.reg_head(feats)
        cls_logits = {k: head(feats) for k, head in self.cls_heads.items()}
        return reg, cls_logits