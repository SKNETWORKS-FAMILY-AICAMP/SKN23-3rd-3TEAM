import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    required?: boolean;
    error?: string;
}

export function Input({ label, required, error, className = "", ...props }: InputProps) {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = props.type === "password";
    const inputType = isPassword ? (showPassword ? "text" : "password") : props.type;

    const borderClass = error
        ? "border-red-300 focus:border-red-400"
        : "border-gray-200 focus:border-onyou focus:bg-white";

    return (
        <div>
            {label && (
                <label className="text-xs font-medium text-gray-500 block mb-1.5">
                    {label}
                    {required && <span className="text-red-400 ml-0.5">*</span>}
                </label>
            )}
            <div className="relative">
                <input
                    {...props}
                    type={inputType}
                    className={`w-full px-4 py-3 border rounded-lg text-sm text-gray-800 placeholder-gray-400 focus:outline-none transition-all ${isPassword ? "pr-11" : ""} ${borderClass} ${className}`}
                />
                {isPassword && (
                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1 cursor-pointer"
                    >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                )}
            </div>
            {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
        </div>
    );
}
