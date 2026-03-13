import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";

interface ToastOptions {
    message: string;
    duration?: number;
    action?: { label: string; onClick: () => void };
}

interface ToastState extends ToastOptions {
    id: number;
}

/**
 * 사용법:
 *   const { toast, ToastContainer } = useToast();
 *   toast({ message: "저장되었습니다!" });
 *   toast({ message: "오류 발생", duration: 5000 });
 *   toast({ message: "로그인이 필요합니다", action: { label: "로그인", onClick: () => navigate("/login") } });
 *
 *   return (
 *     <>
 *       <ToastContainer />
 *       ...
 *     </>
 *   );
 */
export function useToast() {
    const [toasts, setToasts] = useState<ToastState[]>([]);
    const counterRef = useRef(0);

    const dismiss = useCallback((id: number) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const toast = useCallback(({ message, duration = 3000, action }: ToastOptions) => {
        const id = ++counterRef.current;

        setToasts((prev) => [...prev, { id, message, duration, action }]);
        setTimeout(() => dismiss(id), duration);
    }, [dismiss]);

    function ToastContainer() {
        return (
            <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 items-center pointer-events-none">
                <AnimatePresence>
                    {toasts.map((t) => (
                        <motion.div
                            key={t.id}
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 16 }}
                            transition={{ duration: 0.2 }}
                            className="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl shadow-lg text-sm bg-[#1F2937] text-white"
                            style={{ minWidth: "260px", maxWidth: "340px" }}
                        >
                            <span className="flex-1 text-sm leading-relaxed">{t.message}</span>
                            {t.action && (
                                <button
                                    onClick={() => { t.action!.onClick(); dismiss(t.id); }}
                                    className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold bg-onyou text-white transition-all"
                                >
                                    {t.action.label}
                                </button>
                            )}
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        );
    }

    return { toast, ToastContainer };
}
