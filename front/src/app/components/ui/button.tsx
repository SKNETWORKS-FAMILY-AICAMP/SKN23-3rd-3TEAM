import { motion } from "motion/react";
import { Link } from "react-router";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "primary" | "secondary" | "ghost";
    isLoading?: boolean;
    loadingText?: string;
    fullWidth?: boolean;
    to?: string;
}

export function Button({
    variant = "primary",
    isLoading = false,
    loadingText,
    fullWidth = true,
    disabled,
    children,
    className = "",
    to,
    onClick,
    ...props
}: ButtonProps) {
    const base = "py-3 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2";
    const width = fullWidth ? "w-full" : "";

    const variants = {
        primary: `text-white ${disabled || isLoading ? "bg-gray-400" : "bg-onyou"}`,
        secondary: "text-gray-600 bg-gray-100 hover:bg-gray-200",
        ghost: "text-gray-400 hover:text-gray-600",
    };

    const combinedClass = `${base} ${width} ${variants[variant]} ${className}`;
    const content = isLoading ? (
        <>
            <Loader2 className="w-4 h-4 animate-spin" />
            {loadingText ?? children}
        </>
    ) : children;

    if (to) {
        return (
            <motion.div whileTap={{ scale: 0.98 }} className={fullWidth ? "w-full" : ""}>
                <Link to={to} onClick={onClick as unknown as React.MouseEventHandler<HTMLAnchorElement>} className={combinedClass}>
                    {content}
                </Link>
            </motion.div>
        );
    }

    return (
        <motion.button
            whileTap={{ scale: 0.98 }}
            disabled={disabled || isLoading}
            onClick={onClick}
            className={combinedClass}
            {...(props as React.ComponentProps<typeof motion.button>)}
        >
            {content}
        </motion.button>
    );
}
