import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Eye, EyeOff, Leaf, AlertCircle } from "lucide-react";
import { motion } from "motion/react";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const isValid = email.length > 0 && password.length >= 6;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setIsLoading(true);
    setError("");
    await new Promise((r) => setTimeout(r, 1500));
    setIsLoading(false);
    navigate("/chat");
  };

  const handleSocialLogin = (provider: string) => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      navigate("/chat");
    }, 1000);
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
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg"
            style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)" }}
          >
            <Leaf className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-gray-900 font-bold">SKIN AI</h1>
          <p className="text-sm text-gray-500 mt-1">나만의 AI 피부 분석 서비스</p>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-7">
          <h2 className="text-gray-900 font-semibold mb-6">로그인</h2>

          {error && (
            <div className="flex items-center gap-2 px-3 py-2.5 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600 mb-4">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-gray-500 block mb-1.5">이메일</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="이메일을 입력하세요"
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] focus:bg-white transition-all"
                autoComplete="email"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 block mb-1.5">비밀번호</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="비밀번호를 입력하세요"
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] focus:bg-white transition-all pr-11"
                  autoComplete="current-password"
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

            <motion.button
              type="submit"
              disabled={!isValid || isLoading}
              whileTap={{ scale: 0.98 }}
              className={`w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 mt-2 ${
                isValid && !isLoading ? "opacity-100" : "opacity-60 cursor-not-allowed"
              }`}
              style={
                isValid && !isLoading
                  ? { background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" }
                  : { background: "#9CA3AF" }
              }
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  로그인 중...
                </span>
              ) : (
                "로그인"
              )}
            </motion.button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-gray-100" />
            <span className="text-xs text-gray-400">또는 소셜 계정으로 로그인</span>
            <div className="flex-1 h-px bg-gray-100" />
          </div>

          {/* Social Login — icon only, single row */}
          <div className="flex justify-center gap-4">
            {/* Google */}
            <button
              onClick={() => handleSocialLogin("google")}
              className="w-12 h-12 rounded-2xl bg-white border border-gray-200 flex items-center justify-center hover:border-gray-300 hover:shadow-md transition-all"
              title="Google로 로그인"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
            </button>

            {/* Kakao */}
            <button
              onClick={() => handleSocialLogin("kakao")}
              className="w-12 h-12 rounded-2xl flex items-center justify-center hover:opacity-90 hover:shadow-md transition-all"
              style={{ background: "#FEE500" }}
              title="카카오로 로그인"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#3C1E1E">
                <path d="M12 3C7.03 3 3 6.32 3 10.4c0 2.62 1.74 4.92 4.35 6.23l-.9 3.37 3.91-2.57C11.07 17.49 11.53 17.5 12 17.5c4.97 0 9-3.32 9-7.4S16.97 3 12 3z" />
              </svg>
            </button>

            {/* Naver */}
            <button
              onClick={() => handleSocialLogin("naver")}
              className="w-12 h-12 rounded-2xl flex items-center justify-center hover:opacity-90 hover:shadow-md transition-all"
              style={{ background: "#03C75A" }}
              title="네이버로 로그인"
            >
              <span className="text-white font-black text-lg leading-none">N</span>
            </button>
          </div>

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