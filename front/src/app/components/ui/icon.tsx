// SVG 아이콘 컴포넌트
// 사용법: <Icon name="chat" variant="white" size={24} className="..." />

import poreSvg from "@/assets/icons/pore.svg";
import sendActiveSvg from "@/assets/icons/send_active.svg";
import sendDisableSvg from "@/assets/icons/send_disabled.svg";
import chatSvg from "@/assets/icons/chat.svg";
import saveSvg from "@/assets/icons/save.svg";
import wishSvg from "@/assets/icons/wish.svg";
import beautySvg from "@/assets/icons/beauty.svg";
import wrinkleSvg from "@/assets/icons/wrinkle.svg";
import moistureSvg from "@/assets/icons/moisture.svg";
import elasticitySvg from "@/assets/icons/elasticity.svg";
import pigmentationSvg from "@/assets/icons/pigmentation.svg";

export type IconName = "pore" | "send_active" | "send_disable" | "chat" | "save" | "wish" | "beauty" | "wrinkle" | "moisture" | "elasticity" | "pigmentation";
export type IconVariant = "green" | "white";

interface IconProps {
  name: IconName;
  variant?: IconVariant;
  size?: number | string;
  className?: string;
}

const ICON_SRC: Record<IconName, string> = {
  pore:           poreSvg,
  send_active:    sendActiveSvg,
  send_disable:   sendDisableSvg,
  chat:           chatSvg,
  save:           saveSvg,
  wish:           wishSvg,
  beauty:         beautySvg,
  wrinkle:        wrinkleSvg,
  moisture:       moistureSvg,
  elasticity:     elasticitySvg,
  pigmentation:   pigmentationSvg
};

// green → 원본 그대로, white → brightness(0) invert(1) 필터로 흰색 변환
const VARIANT_FILTER: Record<IconVariant, string | undefined> = {
  green: undefined,
  white: "brightness(0) invert(1)",
};

export function Icon({ name, variant = "green", size = 22, className }: IconProps) {
  const px = typeof size === "number" ? `${size}px` : size;

  return (
    <img
      src={ICON_SRC[name]}
      alt={name}
      className={className}
      style={{
        width: px,
        height: px,
        flexShrink: 0,
        filter: VARIANT_FILTER[variant],
      }}
    />
  );
}
