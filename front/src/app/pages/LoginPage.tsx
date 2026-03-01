import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Eye, EyeOff, AlertCircle } from "lucide-react";
import { motion } from "motion/react";
import logoIdle from "@/assets/animations/logo_idle_1.webm";
import { login } from "@/app/api/userApi";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail]             = useState("");
  const [password, setPassword]       = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading]     = useState(false);
  const [error, setError]             = useState("");

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
        <div className="text-center mb-8">
          <h1 className="text-gray-900 font-bold text-[#84c13d]">SKIN AI</h1>
          <p className="text-sm text-gray-500 mt-1">나만의 AI 피부 분석 서비스</p>
          <div className="flex items-center justify-center mx-auto mb-3">
            <video src={logoIdle} autoPlay loop muted playsInline className="w-40 h-auto" />
          </div>
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
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] focus:bg-white transition-all"
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
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] focus:bg-white transition-all pr-11"
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
                <Link
                  to="/forgot-password"
                  className="text-xs text-gray-400 hover:text-[#84C13D] transition-colors"
                >
                  비밀번호 찾기
                </Link>
              </div>
            </div>

            {/* 로그인 버튼 */}
            <motion.button
              type="submit"
              disabled={!isValid || isLoading}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 mt-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
              style={
                isValid && !isLoading
                  ? { background: "#84c13d" }
                  : { background: "#9CA3AF" }
              }
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
            <Link to="/signup" className="font-medium hover:underline" style={{ color: "#84C13D" }}>
              회원가입
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-gray-400 mt-5 leading-relaxed">
          로그인함으로써{" "}
          <span className="underline cursor-pointer hover:text-[#84C13D]">이용약관</span>
          {" "}및{" "}
          <span className="underline cursor-pointer hover:text-[#84C13D]">개인정보 처리방침</span>
          에 동의합니다.
        </p>
      </motion.div>
    </div>
  );
}
