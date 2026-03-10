import { motion } from "motion/react";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface AlertProps {
    message: string;
    variant?: "error" | "success";
    className?: string;
}

export function Alert({ message, variant = "error", className = "" }: AlertProps) {
    const styles = {
        error: "bg-red-50 border-red-100 text-red-600",
        success: "bg-green-50 border-green-100 text-green-600",
    };

    const Icon = variant === "error" ? AlertCircle : CheckCircle2;

    return (
        <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex items-center gap-2 px-3 py-2.5 border rounded-xl text-sm ${styles[variant]} ${className}`}
        >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {message}
        </motion.div>
    );
}
