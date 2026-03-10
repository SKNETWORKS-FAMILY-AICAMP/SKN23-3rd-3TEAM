// SVG 봇 이미지 컴포넌트
// 사용법: <Bot size={24} className="..." />

import BotSvg from "@/assets/bot.svg";

export type IconName = "bot";

interface IconProps {
    size?: number | string;
    className?: string;
}

const BOT_SRC: Record<IconName, string> = {
    bot: BotSvg
};

export function Bot({ size = 34, className }: IconProps) {
    const px = typeof size === "number" ? `${size}px` : size;

    return (
        <div className={className} style={{ width: px, height: px, flexShrink: 0 }}>
            <img src={BOT_SRC['bot']} className='w-full h-full' />
        </div>
    );
}
