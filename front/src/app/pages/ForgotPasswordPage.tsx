import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router";
import { Leaf, Mail, Eye, EyeOff, Check, ChevronLeft, AlertCircle, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import * as authApi from "../api/authApi";

const TIMER_SECONDS = 600; // 10분

function PasswordStrengthBar({ password }: { password: string }) {
  const checks = [
    password.length >= 8,
    /[a-zA-Z]/.test(password),
    /[0-9]/.test(password),
    /[!@#$%^&*]/.test(password),
  ];
  const strength = checks.filter(Boolean).length;
  const colors = ["", "#EF4444", "#F59E0B", "#84C13D", "#10B981"];
  const labels = ["", "약함", "보통", "강함", "매우 강함"];
  return (
    <div className="mt-2">
      <div className="flex gap-1 mb-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="flex-1 h-1.5 rounded-full transition-all"
            style={{ background: i <= strength ? colors[strength] : "#E5E7EB" }}
          />
        ))}
      </div>
      {password && (
        <p className="text-[11px] font-medium" style={{ color: colors[strength] }}>
          {labels[strength]}
        </p>
      )}
    </div>
  );
}

/** 초 → "M:SS" 포맷 */
function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);

  // 이메일 / 코드
  const [email, setEmail] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [code, setCode] = useState("");
  const [codeVerified, setCodeVerified] = useState(false);

  // 새 비밀번호
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // 로딩 / 에러
  const [isSending, setIsSending] = useState(false);   // 발송 버튼
  const [isLoading, setIsLoading] = useState(false);    // 확인·재설정 버튼
  const [sendError, setSendError] = useState("");
  const [codeError, setCodeError] = useState("");
  const [resetError, setResetError] = useState("");

  // 카운트다운 타이머
  const [timeLeft, setTimeLeft] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /** 타이머 시작 (재발송 시에도 재호출) */
  const startTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setTimeLeft(TIMER_SECONDS);
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current!);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
  };

  // 언마운트 시 타이머 정리
  useEffect(() => {
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0;
  const isNewPasswordValid =
    newPassword.length >= 8 &&
    /[a-zA-Z]/.test(newPassword) &&
    /[0-9]/.test(newPassword);
  const canReset = isNewPasswordValid && passwordsMatch;

  /** 인증 코드 발송 */
  const handleSendCode = async () => {
    if (!email) return;
    setSendError("");
    setIsSending(true);
    try {
      await authApi.sendEmailCode(email);
      setCodeSent(true);
      setCode("");
      setCodeError("");
      startTimer();
    } catch (e) {
      setSendError(e instanceof Error ? e.message : "발송에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSending(false);
    }
  };

  /** 인증 코드 확인 */
  const handleVerifyCode = async () => {
    setCodeError("");
    if (code.length < 6) {
      setCodeError("6자리 인증 코드를 입력해주세요");
      return;
    }
    setIsLoading(true);
    try {
      const valid = await authApi.verifyEmailCode(email, code);
      if (valid) {
        setCodeVerified(true);
        if (timerRef.current) clearInterval(timerRef.current);
        setStep(1);
      } else {
        setCodeError("인증 코드가 올바르지 않거나 만료되었습니다.");
      }
    } catch (e) {
      setCodeError(e instanceof Error ? e.message : "확인에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  /** 비밀번호 재설정 */
  const handleResetPassword = async () => {
    if (!canReset) return;
    setResetError("");
    setIsLoading(true);
    try {
      await authApi.resetPassword(email, code, newPassword);
      setStep(2);
    } catch (e) {
      setResetError(e instanceof Error ? e.message : "재설정에 실패했습니다. 처음부터 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FBF3] flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-[400px]"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg"
            style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)" }}
          >
            <Leaf className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-gray-900 font-bold">SKIN AI</h1>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-7">
          <div className="flex items-center gap-2 mb-5">
            {step < 2 && (
              <button
                onClick={() => step > 0 ? setStep(step - 1) : navigate("/login")}
                className="p-1.5 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <ChevronLeft className="w-4 h-4 text-gray-500" />
              </button>
            )}
            <h2 className="font-semibold text-gray-800">
              {step === 0 ? "비밀번호 찾기" : step === 1 ? "새 비밀번호 설정" : "재설정 완료"}
            </h2>
          </div>

          <AnimatePresence mode="wait">
            {/* ── Step 0: 이메일 인증 ── */}
            {step === 0 && (
              <motion.div
                key="step0"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="space-y-4"
              >
                <p className="text-sm text-gray-500">
                  가입한 이메일을 입력하시면 인증 코드를 보내드립니다.
                </p>

                {/* 이메일 입력 + 발송 버튼 */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">이메일</label>
                  <div className="flex gap-2">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        setSendError("");
                      }}
                      onKeyDown={(e) => e.key === "Enter" && !codeSent && handleSendCode()}
                      placeholder="가입한 이메일 주소"
                      disabled={codeVerified}
                      className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] transition-all disabled:opacity-60"
                    />
                    <button
                      onClick={handleSendCode}
                      disabled={!email || isSending || codeVerified}
                      className="px-3 py-3 rounded-xl text-xs font-semibold text-white whitespace-nowrap disabled:opacity-50 min-w-[72px] transition-all"
                      style={{ background: "#84C13D" }}
                    >
                      {isSending ? (
                        <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                      ) : codeSent ? "재발송" : "발송"}
                    </button>
                  </div>

                  {/* 발송 에러 */}
                  {sendError && (
                    <p className="flex items-center gap-1 text-[11px] text-red-400 mt-1.5">
                      <AlertCircle className="w-3 h-3 flex-shrink-0" />{sendError}
                    </p>
                  )}
                </div>

                {/* ── 코드 입력 영역 (발송 후 표시) ── */}
                <AnimatePresence>
                  {codeSent && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="space-y-2 overflow-hidden"
                    >
                      {/* 발송 확인 배너 */}
                      <div className="flex items-center gap-1.5 text-xs text-[#84C13D] bg-[#E8F5D0] px-3 py-2 rounded-xl">
                        <Mail className="w-3.5 h-3.5 flex-shrink-0" />
                        <span>
                          <span className="font-semibold">{email}</span>로 인증 코드가 발송되었습니다
                        </span>
                      </div>

                      <div>
                        <label className="text-xs font-medium text-gray-500 block mb-1.5">인증 코드</label>
                        <input
                          value={code}
                          onChange={(e) => {
                            setCode(e.target.value.replace(/\D/g, ""));
                            setCodeError("");
                          }}
                          onKeyDown={(e) => e.key === "Enter" && handleVerifyCode()}
                          placeholder="6자리 인증 코드 입력"
                          maxLength={6}
                          inputMode="numeric"
                          className={`w-full px-4 py-3 bg-gray-50 border rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none transition-all tracking-widest font-mono ${
                            codeError
                              ? "border-red-300 focus:border-red-400"
                              : "border-gray-200 focus:border-[#84C13D]"
                          }`}
                        />

                        {/* 코드 에러 */}
                        {codeError && (
                          <p className="flex items-center gap-1 text-[11px] text-red-400 mt-1">
                            <AlertCircle className="w-3 h-3 flex-shrink-0" />{codeError}
                          </p>
                        )}

                        {/* 카운트다운 */}
                        <div className="flex items-center justify-between mt-1">
                          <p className="text-[11px] text-gray-400">
                            코드 유효 시간:{" "}
                            <span
                              className="font-semibold"
                              style={{ color: timeLeft > 60 ? "#84C13D" : "#EF4444" }}
                            >
                              {timeLeft > 0 ? formatTime(timeLeft) : "만료됨"}
                            </span>
                          </p>
                          {timeLeft === 0 && (
                            <button
                              onClick={handleSendCode}
                              disabled={isSending}
                              className="text-[11px] text-[#84C13D] font-medium hover:underline disabled:opacity-50"
                            >
                              재발송
                            </button>
                          )}
                        </div>
                      </div>

                      {/* 코드 확인 버튼 */}
                      <button
                        onClick={handleVerifyCode}
                        disabled={!code || isLoading || timeLeft === 0}
                        className="w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-50"
                        style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" }}
                      >
                        {isLoading ? (
                          <span className="flex items-center justify-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            확인 중...
                          </span>
                        ) : "인증 코드 확인"}
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* 최초 발송 버튼 (코드 미발송 상태) */}
                {!codeSent && (
                  <button
                    onClick={handleSendCode}
                    disabled={!email || isSending}
                    className="w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-50"
                    style={email ? { background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" } : { background: "#D1D5DB" }}
                  >
                    {isSending ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        발송 중...
                      </span>
                    ) : "인증 코드 발송"}
                  </button>
                )}
              </motion.div>
            )}

            {/* ── Step 1: 새 비밀번호 설정 ── */}
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="space-y-4"
              >
                <p className="text-sm text-gray-500">새로운 비밀번호를 설정해 주세요.</p>

                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs font-medium text-gray-500 mb-1.5">비밀번호 규칙</p>
                  <ul className="space-y-1">
                    {[
                      { label: "8자 이상", pass: newPassword.length >= 8 },
                      { label: "영문 포함", pass: /[a-zA-Z]/.test(newPassword) },
                      { label: "숫자 포함", pass: /[0-9]/.test(newPassword) },
                    ].map((rule) => (
                      <li key={rule.label} className={`flex items-center gap-1.5 text-[11px] ${rule.pass ? "text-[#84C13D]" : "text-gray-400"}`}>
                        <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${rule.pass ? "bg-[#84C13D]" : "bg-gray-200"}`}>
                          {rule.pass && <Check className="w-2.5 h-2.5 text-white" />}
                        </div>
                        {rule.label}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">새 비밀번호</label>
                  <div className="relative">
                    <input
                      type={showNew ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="새 비밀번호"
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] transition-all pr-11"
                    />
                    <button type="button" onClick={() => setShowNew(!showNew)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 p-1">
                      {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {newPassword && <PasswordStrengthBar password={newPassword} />}
                </div>

                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">새 비밀번호 확인</label>
                  <div className="relative">
                    <input
                      type={showConfirm ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="새 비밀번호 재입력"
                      className={`w-full px-4 py-3 bg-gray-50 border rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none transition-all pr-11 ${
                        confirmPassword
                          ? passwordsMatch ? "border-[#84C13D]" : "border-red-300"
                          : "border-gray-200 focus:border-[#84C13D]"
                      }`}
                    />
                    <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 p-1">
                      {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {confirmPassword && !passwordsMatch && (
                    <p className="text-[11px] text-red-400 mt-1">비밀번호가 일치하지 않습니다</p>
                  )}
                </div>

                {/* 재설정 에러 */}
                {resetError && (
                  <div className="flex items-center gap-2 text-xs text-red-500 bg-red-50 border border-red-100 rounded-xl px-3 py-2.5">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    {resetError}
                  </div>
                )}

                <button
                  onClick={handleResetPassword}
                  disabled={!canReset || isLoading}
                  className="w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-50 mt-2"
                  style={canReset ? { background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" } : { background: "#D1D5DB" }}
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      저장 중...
                    </span>
                  ) : "비밀번호 재설정"}
                </button>
              </motion.div>
            )}

            {/* ── Step 2: 완료 ── */}
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
                  className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-5"
                  style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 8px 24px rgba(133,193,61,0.4)" }}
                >
                  <Check className="w-8 h-8 text-white" />
                </motion.div>
                <h2 className="text-gray-900 font-bold mb-2">재설정 완료!</h2>
                <p className="text-sm text-gray-500 mb-6">
                  비밀번호가 성공적으로 재설정되었습니다.<br />새 비밀번호로 로그인해 주세요.
                </p>
                <button
                  onClick={() => navigate("/login")}
                  className="w-full py-3.5 rounded-xl text-sm font-semibold text-white"
                  style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" }}
                >
                  로그인하러 가기
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {step < 2 && (
          <p className="text-xs text-center text-gray-400 mt-4">
            <Link to="/login" className="hover:text-[#84C13D] transition-colors">
              ← 로그인으로 돌아가기
            </Link>
          </p>
        )}
      </motion.div>
    </div>
  );
}
