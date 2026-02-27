import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Eye, EyeOff, Leaf, Check, X, AlertCircle, Mail } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const STEPS = ["계정 정보", "피부 정보", "완료"];

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: "8자 이상", pass: password.length >= 8 },
    { label: "영문 포함", pass: /[a-zA-Z]/.test(password) },
    { label: "숫자 포함", pass: /[0-9]/.test(password) },
    { label: "특수문자 포함", pass: /[!@#$%^&*]/.test(password) },
  ];
  const strength = checks.filter((c) => c.pass).length;
  const labels = ["", "약함", "보통", "강함", "매우 강함"];
  const colors = ["", "#EF4444", "#F59E0B", "#84C13D", "#10B981"];

  return (
    <div className="mt-2">
      <div className="flex gap-1 mb-1.5">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="flex-1 h-1.5 rounded-full transition-all duration-300"
            style={{ background: i <= strength ? colors[strength] : "#E5E7EB" }}
          />
        ))}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium" style={{ color: strength > 0 ? colors[strength] : "#9CA3AF" }}>
          {strength > 0 ? labels[strength] : "비밀번호를 입력하세요"}
        </span>
        <div className="flex gap-2.5">
          {checks.map((c) => (
            <div key={c.label} className={`flex items-center gap-1 text-[10px] ${c.pass ? "text-[#84C13D]" : "text-gray-300"}`}>
              <Check className="w-2.5 h-2.5" />
              {c.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const SKIN_TYPES = ["건성", "지성", "복합성", "중성", "민감성"];
const SKIN_CONCERNS = ["수분 부족", "모공 케어", "미백", "탄력", "여드름", "색소침착"];

export function SignupPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [email, setEmail] = useState("");
  const [emailVerified, setEmailVerified] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [verifyCode, setVerifyCode] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [name, setName] = useState("");
  const [nickname, setNickname] = useState("");
  const [skinType, setSkinType] = useState("");
  const [concerns, setConcerns] = useState<string[]>([]);
  const [agreed, setAgreed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const passwordChecks = {
    length: password.length >= 8,
    letter: /[a-zA-Z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*]/.test(password),
  };
  const isPasswordStrong = Object.values(passwordChecks).filter(Boolean).length >= 3;
  const passwordMatch = password === passwordConfirm && passwordConfirm.length > 0;

  const step1Valid = email.length > 0 && emailVerified && isPasswordStrong && passwordMatch && agreed;
  const step2Valid = skinType !== "";

  const handleSendEmail = async () => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 1000));
    setEmailSent(true);
    setIsLoading(false);
  };

  const handleVerify = async () => {
    if (verifyCode === "1234" || verifyCode.length >= 4) {
      setEmailVerified(true);
    }
  };

  const handleNext = async () => {
    if (step === 0 && step1Valid) setStep(1);
    else if (step === 1) {
      setIsLoading(true);
      await new Promise((r) => setTimeout(r, 1500));
      setIsLoading(false);
      setStep(2);
    }
  };

  const toggleConcern = (c: string) =>
    setConcerns((prev) => prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]);

  return (
    <div className="min-h-screen bg-[#F8FBF3] flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-[440px]"
      >
        {/* Logo */}
        <div className="text-center mb-7">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg"
            style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)" }}
          >
            <Leaf className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-gray-900 font-bold">SKIN AI 회원가입</h1>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-7">
          <AnimatePresence mode="wait">
            {step === 0 && (
              <motion.div
                key="step0"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <h2 className="text-gray-900 font-semibold mb-4">계정 정보 입력</h2>

                {/* Email */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">
                    이메일 <span className="text-red-400">*</span>
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="이메일 주소"
                      disabled={emailVerified}
                      className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] focus:bg-white transition-all disabled:opacity-60"
                    />
                    <button
                      onClick={handleSendEmail}
                      disabled={!email || emailVerified || isLoading}
                      className="px-3 py-3 rounded-xl text-xs font-semibold text-white whitespace-nowrap disabled:opacity-50 transition-all"
                      style={{ background: emailVerified ? "#10B981" : "#84C13D", minWidth: "80px" }}
                    >
                      {emailVerified ? (
                        <span className="flex items-center gap-1"><Check className="w-3.5 h-3.5" />인증완료</span>
                      ) : emailSent ? "재발송" : "인증발송"}
                    </button>
                  </div>
                  {emailSent && !emailVerified && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-2">
                      <div className="flex items-center gap-1.5 text-xs text-[#84C13D] mb-1.5">
                        <Mail className="w-3 h-3" />
                        인증 코드가 이메일로 발송되었습니다
                      </div>
                      <div className="flex gap-2">
                        <input
                          value={verifyCode}
                          onChange={(e) => setVerifyCode(e.target.value)}
                          placeholder="인증 코드 입력 (예: 1234)"
                          maxLength={6}
                          className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-[#84C13D] transition-all"
                        />
                        <button
                          onClick={handleVerify}
                          className="px-4 py-3 rounded-xl text-xs font-semibold text-white"
                          style={{ background: "#84C13D" }}
                        >
                          확인
                        </button>
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* Password */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">
                    비밀번호 <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="비밀번호"
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] focus:bg-white transition-all pr-11"
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 p-1">
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {password && <PasswordStrength password={password} />}
                </div>

                {/* Password Confirm */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">
                    비밀번호 확인 <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirm ? "text" : "password"}
                      value={passwordConfirm}
                      onChange={(e) => setPasswordConfirm(e.target.value)}
                      placeholder="비밀번호 재입력"
                      className={`w-full px-4 py-3 bg-gray-50 border rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none transition-all pr-11 ${
                        passwordConfirm
                          ? passwordMatch
                            ? "border-[#84C13D] focus:border-[#84C13D]"
                            : "border-red-300 focus:border-red-400"
                          : "border-gray-200 focus:border-[#84C13D]"
                      }`}
                    />
                    <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 p-1">
                      {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                    {passwordConfirm && (
                      <div className="absolute right-9 top-1/2 -translate-y-1/2">
                        {passwordMatch ? (
                          <Check className="w-4 h-4 text-[#84C13D]" />
                        ) : (
                          <X className="w-4 h-4 text-red-400" />
                        )}
                      </div>
                    )}
                  </div>
                  {passwordConfirm && !passwordMatch && (
                    <p className="text-[11px] text-red-400 mt-1">비밀번호가 일치하지 않습니다</p>
                  )}
                </div>

                {/* Name */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">이름 <span className="text-red-400">*</span></label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="실명 입력"
                    maxLength={20}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] transition-all"
                  />
                </div>

                {/* Nickname */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">닉네임</label>
                  <input
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    placeholder="닉네임 (선택)"
                    maxLength={12}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] transition-all"
                  />
                </div>

                {/* Agreement */}
                <label className="flex items-start gap-3 cursor-pointer group">
                  <div
                    className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all ${
                      agreed ? "border-transparent" : "border-gray-300 group-hover:border-[#84C13D]"
                    }`}
                    style={agreed ? { background: "#84C13D" } : {}}
                    onClick={() => setAgreed(!agreed)}
                  >
                    {agreed && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <span className="text-xs text-gray-500 leading-relaxed">
                    <span className="text-[#84C13D] font-medium underline cursor-pointer">이용약관</span> 및{" "}
                    <span className="text-[#84C13D] font-medium underline cursor-pointer">개인정보 처리방침</span>에 동의합니다 (필수)
                  </span>
                </label>

                <button
                  onClick={handleNext}
                  disabled={!step1Valid}
                  className="w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                  style={step1Valid ? { background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" } : { background: "#D1D5DB" }}
                >
                  다음 단계
                </button>
              </motion.div>
            )}

            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-5"
              >
                <h2 className="text-gray-900 font-semibold mb-4">피부 정보 입력</h2>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-2">피부 타입 <span className="text-red-400">*</span></label>
                  <div className="flex flex-wrap gap-2">
                    {SKIN_TYPES.map((type) => (
                      <button
                        key={type}
                        onClick={() => setSkinType(type)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium border-2 transition-all ${
                          skinType === type ? "text-white border-transparent" : "border-gray-200 text-gray-600 hover:border-[#84C13D]"
                        }`}
                        style={skinType === type ? { background: "#84C13D" } : {}}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-2">피부 고민 (선택)</label>
                  <div className="flex flex-wrap gap-2">
                    {SKIN_CONCERNS.map((c) => (
                      <button
                        key={c}
                        onClick={() => toggleConcern(c)}
                        className={`px-3 py-2 rounded-xl text-sm font-medium border-2 transition-all flex items-center gap-1 ${
                          concerns.includes(c) ? "border-transparent text-white" : "border-gray-200 text-gray-600 hover:border-[#84C13D]"
                        }`}
                        style={concerns.includes(c) ? { background: "#84C13D" } : {}}
                      >
                        {concerns.includes(c) && <Check className="w-3 h-3" />}
                        {c}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => setStep(0)}
                    className="flex-1 py-3.5 rounded-xl text-sm font-semibold text-gray-600 border-2 border-gray-200 hover:border-gray-300 transition-all"
                  >
                    이전
                  </button>
                  <button
                    onClick={handleNext}
                    disabled={!step2Valid || isLoading}
                    className="flex-1 py-3.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-50"
                    style={step2Valid ? { background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" } : { background: "#D1D5DB" }}
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        처리 중...
                      </span>
                    ) : (
                      "가입 완료"
                    )}
                  </button>
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-4"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", damping: 12, delay: 0.2 }}
                  className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-5"
                  style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 8px 24px rgba(133,193,61,0.4)" }}
                >
                  <Check className="w-10 h-10 text-white" />
                </motion.div>
                <h2 className="text-gray-900 font-bold mb-2">가입 완료!</h2>
                <p className="text-sm text-gray-500 mb-6">SKIN AI에 오신 것을 환영합니다 🌿<br />AI 피부 분석을 시작해 보세요!</p>
                <button
                  onClick={() => navigate("/chat")}
                  className="w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all"
                  style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" }}
                >
                  시작하기
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {step < 2 && (
          <p className="text-xs text-center text-gray-400 mt-4">
            이미 계정이 있으신가요?{" "}
            <Link to="/login" className="font-medium hover:underline" style={{ color: "#84C13D" }}>
              로그인
            </Link>
          </p>
        )}
      </motion.div>
    </div>
  );
}