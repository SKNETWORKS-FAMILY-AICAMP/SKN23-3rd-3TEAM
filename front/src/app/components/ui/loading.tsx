import { motion } from "motion/react";
import loadingWebm from "@/assets/animations/logo_loop_1.webm";

export type LodingType = "page";

interface LoadingProps {
    size?: number | string;
    className?: string;
}

export function Loading({ size=120, className}: LoadingProps) {
    return (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={`flex flex-col items-center justify-center ${className}`}>
            <video src={loadingWebm} autoPlay loop muted playsInline style={{width: `${size}px`, height: `${size}px`}} />
            <p className="text-sm text-gray-500">불러오는 중...</p>
        </motion.div>
    )
}