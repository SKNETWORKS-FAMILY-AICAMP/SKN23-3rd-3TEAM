import { motion } from "motion/react";
import LoadingWebm from "@/assets/animations/logo_loop_1.webm";

export type LodingType = "page";

interface LoadingProps {
    size?: number | string;
    className?: string;
}

export function Loading({ size=140, className}: LoadingProps) {
    return (
        <div className="h-full flex items-center justify-center">
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={`flex flex-col items-center justify-center ${className}`}>
                <video src={LoadingWebm} autoPlay loop muted playsInline style={{width: `${size}px`, height: `${size}px`}} />
                <p className="text-sm text-gray-500">불러오는 중...</p>
            </motion.div>
        </div>
    )
}