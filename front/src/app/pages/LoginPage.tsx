import { motion } from "motion/react";
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router";
import { Eye, EyeOff, AlertCircle } from "lucide-react";
import { login, startSocialLogin } from "@/app/api/authApi";
import LogoIdle from "@/assets/animations/logo_idle_1.webm";

export function LoginPage() {
    const navigate = useNavigate();
    const [email, setEmail]                 = useState("");
    const [password, setPassword]           = useState("");
    const [showPassword, setShowPassword]   = useState(false);
    const [isLoading, setIsLoading]         = useState(false);
    const [error, setError]                 = useState("");

    // OAuth 실패 시 /login?error=... 로 리디렉션되는 경우 에러 표시
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const oauthError = params.get("error");

        if (oauthError) setError(decodeURIComponent(oauthError));
    }, []);

    const isValid = email.length > 0 && password.length >= 1;

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!isValid || isLoading) return;

        setIsLoading(true);
        setError("");

        try {
            await login(email, password);

            navigate("/chat", { replace: true });
        } catch (err) {
            setError(err instanceof Error ? err.message : "로그인에 실패했습니다.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F8FBF3] flex items-center justify-center px-4 py-12">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="w-full max-w-[400px]"
            >
                {/* Logo */}
                <div className="text-center mb-2">
                    <p className="text-4xl font-bold text-onyou">On_You</p>
                    <p className="text-sm text-gray-500 mt-1">나만의 AI 피부 분석 서비스</p>
                    <Link to="/chat" className="flex items-center justify-center mx-auto my-3">
                        <video src={LogoIdle} autoPlay loop muted playsInline className="w-30 h-auto" />
                    </Link>
                </div>

                <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-7">
                    <h2 className="text-gray-900 font-semibold mb-6 text-center">로그인</h2>

                    {/* 에러 메시지 */}
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: -6 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-center gap-2 px-3 py-2.5 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600 mb-4"
                        >
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            {error}
                        </motion.div>
                    )}

                    <form onSubmit={handleLogin} className="space-y-4">
                        {/* 이메일 */}
                        <div>
                            <label className="text-xs font-medium text-gray-500 block mb-1.5">이메일</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => { setEmail(e.target.value); setError(""); }}
                                placeholder="이메일을 입력하세요"
                                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-onyou focus:bg-white transition-all"
                                autoComplete="email"
                                disabled={isLoading}
                            />
                        </div>

                        {/* 비밀번호 */}
                        <div>
                            <label className="text-xs font-medium text-gray-500 block mb-1.5">비밀번호</label>
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => { setPassword(e.target.value); setError(""); }}
                                    placeholder="비밀번호를 입력하세요"
                                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-onyou focus:bg-white transition-all pr-11"
                                    autoComplete="current-password"
                                    disabled={isLoading}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                            <div className="flex justify-end mt-1.5">
                                <Link to="/forgot-password"className="text-xs text-gray-400 hover:text-onyou transition-colors">
                                    비밀번호 찾기
                                </Link>
                            </div>
                        </div>

                        {/* 로그인 버튼 */}
                        <motion.button
                            type="submit"
                            disabled={!isValid || isLoading}
                            whileTap={{ scale: 0.98 }}
                            className={`w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 mt-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed ${isValid && !isLoading ? "bg-onyou" : "bg-gray-400"}`}
                        >
                            {isLoading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    로그인 중...
                                </span>
                            ) : "로그인"}
                        </motion.button>
                    </form>

                    <p className="text-xs text-center text-gray-400 mt-5">
                        계정이 없으신가요?{" "}
                        <Link to="/signup" className="font-medium hover:underline text-onyou">
                            회원가입
                        </Link>
                    </p>

                    {/* 구분선 */}
                    <div className="flex items-center gap-3 my-5">
                        <div className="flex-1 h-px bg-gray-100" />
                        <span className="text-xs text-gray-300 font-medium">또는</span>
                        <div className="flex-1 h-px bg-gray-100" />
                    </div>

                    {/* 소셜 로그인 */}
                    <div className="flex justify-center gap-3">
                        {/* 구글 로그인 */}
                        <button
                            type="button"
                            onClick={() => startSocialLogin("google")}
                            aria-label="구글로 로그인"
                            className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-200 bg-white transition-all duration-200 cursor-pointer hover:bg-gray-50 active:scale-95"
                        >
                            <svg width="20" height="20" viewBox="0 0 18 18">
                                <path d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4"/>
                                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853"/>
                                <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z" fill="#FBBC05"/>
                                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z" fill="#EA4335"/>
                            </svg>
                        </button>

                        {/* 카카오 로그인 */}
                        {/* <button
                            type="button"
                            onClick={() => startSocialLogin("kakao")}
                            aria-label="카카오로 로그인"
                            className="w-10 h-10 flex items-center justify-center rounded-full transition-all duration-200 cursor-pointer hover:brightness-95 active:scale-95"
                            style={{ background: "#FEE500" }}
                        >
                            <svg width="22" height="22" viewBox="0 0 18 18" fill="none">
                                <path
                                    d="M9 1.5C4.858 1.5 1.5 4.134 1.5 7.35c0 2.07 1.368 3.888 3.426 4.944L4.05 15.3a.225.225 0 0 0 .33.243l3.6-2.394A8.96 8.96 0 0 0 9 13.2c4.142 0 7.5-2.634 7.5-5.85S13.142 1.5 9 1.5Z"
                                    fill="#000000"
                                    fillOpacity="0.85"
                                />
                            </svg>
                        </button> */}

                        {/* 네이버 로그인 */}
                        <button
                            type="button"
                            onClick={() => startSocialLogin("naver")}
                            aria-label="네이버로 로그인"
                            className="w-10 h-10 flex items-center justify-center rounded-full transition-all duration-200 cursor-pointer hover:brightness-95 active:scale-95"
                            style={{ background: "#03C75A" }}
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M16.273 12.845 7.376 0H0v24h7.727V11.155L16.624 24H24V0h-7.727z" fill="#ffffff" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* <p className="text-center text-xs text-gray-400 mt-5 leading-relaxed">
                    로그인함으로써{" "}
                    <span className="underline cursor-pointer hover:text-onyou">이용약관</span>
                    {" "}및{" "}
                    <span className="underline cursor-pointer hover:text-onyou">개인정보 처리방침</span>
                    에 동의합니다.
                </p> */}
            </motion.div>
        </div>
    );
}
