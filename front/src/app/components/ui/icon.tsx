// SVG 아이콘 컴포넌트
// 사용법: <Icon name="chat" variant="white" size={24} className="..." />

import ChatSvg from "@/assets/icons/chat.svg";
import PoreSvg from "@/assets/icons/pore.svg";
import SaveSvg from "@/assets/icons/save.svg";
import WishSvg from "@/assets/icons/wish.svg";
import BeautySvg from "@/assets/icons/beauty.svg";
import WrinkleSvg from "@/assets/icons/wrinkle.svg";
import MoistureSvg from "@/assets/icons/moisture.svg";
import ElasticitySvg from "@/assets/icons/elasticity.svg";
import SendActiveSvg from "@/assets/icons/send_active.svg";
import SendDisableSvg from "@/assets/icons/send_disabled.svg";
import PigmentationSvg from "@/assets/icons/pigmentation.svg";

export type IconName = "pore" | "send_active" | "send_disable" | "chat" | "save" | "wish" | "beauty" | "wrinkle" | "moisture" | "elasticity" | "pigmentation";
export type IconVariant = "green" | "white";

interface IconProps {
    name: IconName;
    variant?: IconVariant;
    size?: number | string;
    className?: string;
}

const ICON_SRC: Record<IconName, string> = {
    pore:           PoreSvg,
    send_active:    SendActiveSvg,
    send_disable:   SendDisableSvg,
    chat:           ChatSvg,
    save:           SaveSvg,
    wish:           WishSvg,
    beauty:         BeautySvg,
    wrinkle:        WrinkleSvg,
    moisture:       MoistureSvg,
    elasticity:     ElasticitySvg,
    pigmentation:   PigmentationSvg
};

// green → 원본 그대로, white → brightness(0) invert(1) 필터로 흰색 변환
const VARIANT_FILTER: Record<IconVariant, string | undefined> = {
    green: undefined,
    white: "brightness(0) invert(1)",
};

export function Icon({ name, variant = "green", size = 22, className }: IconProps) {
    const px = typeof size === "number" ? `${size}px` : size;

    return (
        <img src={ICON_SRC[name]} alt={name} className={className} style={{ width: px, height: px, flexShrink: 0, filter: VARIANT_FILTER[variant] }} />
    );
}
