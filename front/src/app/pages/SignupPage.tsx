import { useState, useEffect } from "react";
import * as authApi from "../api/authApi";
import * as userApi from "../api/userApi";
import type { KeywordItem } from "../api/userApi";
import { Link, useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import logoIdle from "@/assets/animations/logo_idle_1.webm";
import { Eye, EyeOff, Check, X, AlertCircle, Mail, Loader2, Plus } from "lucide-react";

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

const FALLBACK_SKIN_TYPE_KEYWORDS: KeywordItem[] = [
  { keyword_id: -1, type: "skin_type", keyword: "dry",       label: "건성",  description: null },
  { keyword_id: -2, type: "skin_type", keyword: "oily",      label: "지성",  description: null },
  { keyword_id: -3, type: "skin_type", keyword: "combo",     label: "복합성", description: null },
  { keyword_id: -4, type: "skin_type", keyword: "normal",    label: "중성",  description: null },
  { keyword_id: -5, type: "skin_type", keyword: "sensitive", label: "민감성", description: null },
];
const DEFAULT_CONCERNS = ["각질", "건조", "모공", "미백", "민감", "블랙헤드", "아토피", "유분", "장벽", "주름", "트러블", "피지", "흉터"];

export function SignupPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);

  // 계정 정보
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
  const [agreed, setAgreed] = useState(false);

  // skin_type 키워드 목록 (마운트 시 로드)
  const [skinTypeKeywords, setSkinTypeKeywords] = useState<KeywordItem[]>(FALLBACK_SKIN_TYPE_KEYWORDS);

  useEffect(() => {
    userApi.fetchKeywords("skin_type")
      .then((keywords) => { if (keywords.length > 0) setSkinTypeKeywords(keywords); })
      .catch(() => { /* 폴백 유지 */ });
  }, []);

  // 피부 정보
  const [gender, setGender] = useState<"여성" | "남성" | "">("");
  const [age, setAge] = useState("");
  const [skinType, setSkinType] = useState("");
  const [concerns, setConcerns] = useState<string[]>([]);
  const [customConcerns, setCustomConcerns] = useState<string[]>([]);
  const [showAddConcern, setShowAddConcern] = useState(false);
  const [newConcernInput, setNewConcernInput] = useState("");

  const allConcerns = [...DEFAULT_CONCERNS, ...customConcerns];

  // 로딩 / 에러
  const [isSending, setIsSending] = useState(false);   // 인증 코드 발송 버튼
  const [isVerifying, setIsVerifying] = useState(false); // 코드 확인 버튼
  const [isLoading, setIsLoading] = useState(false);    // 가입 완료 버튼
  const [emailError, setEmailError] = useState("");     // 발송 에러
  const [verifyError, setVerifyError] = useState("");   // 코드 검증 에러
  const [signupError, setSignupError] = useState("");   // 가입 에러

  const passwordChecks = {
    length : password.length >= 8,
    letter : /[a-zA-Z]/.test(password),
    number : /[0-9]/.test(password),
    special: /[!@#$%^&*]/.test(password),
  };
  const isPasswordStrong = Object.values(passwordChecks).filter(Boolean).length >= 3;
  const passwordMatch = password === passwordConfirm && passwordConfirm.length > 0;

  const step1Valid =
    email.length > 0 &&
    emailVerified &&
    name.length > 0 &&
    isPasswordStrong &&
    passwordMatch &&
    agreed;
  const step2Valid = skinType !== "";

  /** 이메일 인증 코드 발송 */
  const handleSendEmail = async () => {
    setEmailError("");
    setIsSending(true);
    try {
      await authApi.sendEmailCode(email);
      setEmailSent(true);
      setEmailVerified(false);
      setVerifyCode("");
      setVerifyError("");
    } catch (e) {
      setEmailError(e instanceof Error ? e.message : "발송에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsSending(false);
    }
  };

  /** 인증 코드 확인 */
  const handleVerify = async () => {
    if (verifyCode.length < 6) {
      setVerifyError("6자리 인증 코드를 입력해 주세요.");
      return;
    }
    setVerifyError("");
    setIsVerifying(true);
    try {
      const valid = await authApi.verifyEmailCode(email, verifyCode);
      if (valid) {
        setEmailVerified(true);
      } else {
        setVerifyError("인증 코드가 올바르지 않거나 만료되었습니다.");
      }
    } catch (e) {
      setVerifyError(e instanceof Error ? e.message : "확인에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsVerifying(false);
    }
  };

  /** 다음 단계 / 가입 완료 */
  const handleNext = async () => {
    if (step === 0 && step1Valid) {
      setStep(1);
      return;
    }
    if (step === 1) {
      setIsLoading(true);
      setSignupError("");
      try {
        // 1. 회원가입 (서버에서 OTP 재검증 포함)
        await authApi.signup({
          email,
          name,
          nickname         : nickname.trim() || name,
          password,
          terms_agreed     : agreed,
          privacy_agreed   : agreed,
          verification_code: verifyCode,
        });

        // 2. 자동 로그인 (토큰 발급)
        await authApi.login(email, password);

        // 3. 프로필 추가 정보 저장 (선택 입력)
        const GENDER_TO_API: Record<string, "male" | "female" | null> = {
          "여성": "female",
          "남성": "male",
          ""    : null,
        };
        const skinKeywordId = skinTypeKeywords.find((k) => k.label === skinType)?.keyword_id ?? null;
        const profileUpdate: Parameters<typeof userApi.updateCurrentUser>[0] = {};
        if (gender)                      profileUpdate.gender       = GENDER_TO_API[gender];
        if (age)                         profileUpdate.age          = Number(age);
        if (skinKeywordId !== null && skinKeywordId > 0) profileUpdate.skin_type = skinKeywordId;
        if (concerns.length)             profileUpdate.skin_concern = concerns.join(",");
        if (Object.keys(profileUpdate).length > 0) {
          await userApi.updateCurrentUser(profileUpdate).catch(() => {});
        }

        setStep(2);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "가입에 실패했습니다. 다시 시도해 주세요.";
        // OTP 만료 에러 → step 0으로 돌아가서 이메일 재인증 유도
        if (msg.includes("인증 코드")) {
          setEmailVerified(false);
          setEmailSent(false);
          setVerifyCode("");
          setVerifyError("");
          setEmailError("인증 코드가 만료되었습니다. 이메일 인증을 다시 진행해 주세요.");
          setSignupError("");
          setStep(0);
        } else {
          setSignupError(msg);
        }
      } finally {
        setIsLoading(false);
      }
    }
  };

  const toggleConcern = (c: string) =>
    setConcerns((prev) => prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]);

  const addCustomConcern = () => {
    const trimmed = newConcernInput.trim();
    if (trimmed && !allConcerns.includes(trimmed)) {
      setCustomConcerns((prev) => [...prev, trimmed]);
      setConcerns((prev) => [...prev, trimmed]);
    }
    setNewConcernInput("");
    setShowAddConcern(false);
  };

  const removeConcern = (c: string) => {
    setCustomConcerns((prev) => prev.filter((x) => x !== c));
    setConcerns((prev) => prev.filter((x) => x !== c));
  };

  return (
    <div className="min-h-screen bg-[#F8FBF3] flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-[440px]"
      >
        {/* Logo */}
        <div className="text-center mb-7">
          <div className="flex items-center justify-center mx-auto mb-3">
            <video src={logoIdle} autoPlay loop muted playsInline className="w-40 h-auto" />
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
                <h2 className="text-gray-900 font-semibold mb-4 text-center">계정 정보 입력</h2>

                {/* ── 이메일 ── */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">
                    이메일 <span className="text-red-400">*</span>
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        setEmailError("");
                        // 이메일 변경 시 인증 상태 초기화
                        if (emailVerified) {
                          setEmailVerified(false);
                          setEmailSent(false);
                        }
                      }}
                      placeholder="이메일 주소"
                      disabled={emailVerified}
                      className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] focus:bg-white transition-all disabled:opacity-60"
                    />
                    <button
                      onClick={handleSendEmail}
                      disabled={!email || emailVerified || isSending}
                      className="px-3 py-3 rounded-xl text-xs font-semibold text-white whitespace-nowrap cursor-pointer disabled:opacity-50 transition-all"
                      style={{ background: emailVerified ? "#10B981" : "#84C13D", minWidth: "80px" }}
                    >
                      {emailVerified ? (
                        <span className="flex items-center gap-1">
                          <Check className="w-3.5 h-3.5" />인증완료
                        </span>
                      ) : isSending ? (
                        <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                      ) : emailSent ? "재발송" : "인증발송"}
                    </button>
                  </div>

                  {/* 발송 에러 */}
                  {emailError && (
                    <p className="flex items-center gap-1 text-[11px] text-red-400 mt-1.5">
                      <AlertCircle className="w-3 h-3 flex-shrink-0" />{emailError}
                    </p>
                  )}

                  {/* ── 코드 입력 영역 ── */}
                  {emailSent && !emailVerified && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="mt-2 overflow-hidden"
                    >
                      <div className="flex items-center gap-1.5 text-xs text-[#84C13D] mb-2">
                        <Mail className="w-3 h-3" />
                        인증 코드가 <span className="font-semibold">{email}</span>로 발송되었습니다
                      </div>
                      <div className="flex gap-2">
                        <input
                          value={verifyCode}
                          onChange={(e) => {
                            setVerifyCode(e.target.value.replace(/\D/g, ""));
                            setVerifyError("");
                          }}
                          onKeyDown={(e) => e.key === "Enter" && handleVerify()}
                          placeholder="6자리 인증 코드 입력"
                          maxLength={6}
                          inputMode="numeric"
                          className={`flex-1 px-4 py-3 bg-gray-50 border rounded-xl text-sm tracking-widest font-mono focus:outline-none transition-all ${
                            verifyError
                              ? "border-red-300 focus:border-red-400"
                              : "border-gray-200 focus:border-[#84C13D]"
                          }`}
                        />
                        <button
                          onClick={handleVerify}
                          disabled={!verifyCode || isVerifying}
                          className="px-4 py-3 rounded-xl text-xs font-semibold text-white disabled:opacity-50 transition-all min-w-[52px]"
                          style={{ background: "#84C13D" }}
                        >
                          {isVerifying ? (
                            <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                          ) : "확인"}
                        </button>
                      </div>

                      {/* 코드 검증 에러 */}
                      {verifyError && (
                        <p className="flex items-center gap-1 text-[11px] text-red-400 mt-1.5">
                          <AlertCircle className="w-3 h-3 flex-shrink-0" />{verifyError}
                        </p>
                      )}

                      <p className="text-[11px] text-gray-400 mt-1.5">
                        코드가 오지 않으면{" "}
                        <button
                          onClick={handleSendEmail}
                          disabled={isSending}
                          className="text-[#84C13D] font-medium hover:underline disabled:opacity-50"
                        >
                          재발송
                        </button>
                        하거나 스팸함을 확인해 주세요.
                      </p>
                    </motion.div>
                  )}
                </div>

                {/* ── 비밀번호 ── */}
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

                {/* ── 비밀번호 확인 ── */}
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

                {/* ── 이름 ── */}
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

                {/* ── 닉네임 ── */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1.5">닉네임</label>
                  <input
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    placeholder="닉네임 (선택, 미입력 시 이름으로 설정)"
                    maxLength={12}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] transition-all"
                  />
                </div>

                {/* ── 약관 동의 ── */}
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
                  className="w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                  style={step1Valid ? { background: "#84C13D", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" } : { background: "#D1D5DB" }}
                >
                  다음 단계
                </button>
              </motion.div>
            )}

            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-5">
                <h2 className="text-gray-900 font-semibold text-center mb-4">피부 정보 입력</h2>

                {/* ── 성별 / 나이 ── */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-2">성별 (선택)</label>
                    <div className="flex gap-2">
                      {(["여성", "남성"] as const).map((g) => (
                        <button
                          key={g}
                          onClick={() => setGender(gender === g ? "" : g)}
                          className={`flex-1 py-2.5 rounded-xl text-xs font-medium border-2 transition-all cursor-pointer ${
                            gender === g
                              ? "border-transparent text-white"
                              : "border-gray-200 text-gray-600 hover:border-[#84C13D]"
                          }`}
                          style={gender === g ? { background: "#84C13D" } : {}}
                        >
                          {g}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-2">나이 (선택)</label>
                    <input
                      type="number"
                      value={age}
                      onChange={(e) => {
                        const v = e.target.value;
                        if (v === "" || (Number(v) >= 1 && Number(v) <= 120)) setAge(v);
                      }}
                      min={1}
                      max={120}
                      placeholder="나이 입력"
                      className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] transition-all"
                    />
                  </div>
                </div>

                {/* ── 구분선 ── */}
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-px bg-gray-100" />
                  <span className="text-[11px] text-gray-400 font-medium">피부 정보</span>
                  <div className="flex-1 h-px bg-gray-100" />
                </div>

                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-2">피부 타입 <span className="text-red-400">*</span></label>
                  <div className="flex flex-wrap gap-2">
                    {skinTypeKeywords.map((k) => {
                      const label = k.label ?? k.keyword;
                      return (
                        <button
                          key={k.keyword_id}
                          onClick={() => setSkinType(label)}
                          className={`px-4 py-2 rounded-xl text-sm font-medium border-2 transition-all cursor-pointer ${
                            skinType === label ? "text-white border-transparent" : "border-gray-200 text-gray-600 hover:border-[#84C13D]"
                          }`}
                          style={skinType === label ? { background: "#84C13D" } : {}}
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-2">피부 고민 (선택)</label>
                  <div className="flex flex-wrap gap-2">
                    {allConcerns.map((c) => {
                      const selected = concerns.includes(c);
                      const isCustom = customConcerns.includes(c);
                      return (
                        <button
                          key={c}
                          onClick={() => toggleConcern(c)}
                          className={`px-3 py-1.5 rounded-xl text-xs font-medium border-2 transition-all flex items-center gap-1.5 cursor-pointer ${
                            selected
                              ? "border-transparent text-white"
                              : "border-gray-200 text-gray-600 hover:border-[#84C13D]"
                          }`}
                          style={selected ? { background: "#84C13D" } : {}}
                        >
                          {selected && <Check className="w-3 h-3 flex-shrink-0" />}
                          {c}
                          {isCustom && (
                            <span
                              className="ml-0.5"
                              onClick={(e) => { e.stopPropagation(); removeConcern(c); }}
                            >
                              <X className="w-3 h-3" />
                            </span>
                          )}
                        </button>
                      );
                    })}

                    {/* '+추가' 버튼 */}
                    {!showAddConcern && (
                      <button
                        onClick={() => setShowAddConcern(true)}
                        className="px-3 py-1.5 rounded-xl text-xs font-medium border-2 border-dashed border-gray-300 text-gray-400 cursor-pointer hover:border-[#84C13D] hover:text-[#84C13D] transition-all flex items-center gap-1"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        추가
                      </button>
                    )}
                  </div>

                  {/* 커스텀 키워드 입력 */}
                  <AnimatePresence>
                    {showAddConcern && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-2 flex gap-2 overflow-hidden"
                      >
                        <input
                          autoFocus
                          value={newConcernInput}
                          onChange={(e) => setNewConcernInput(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") addCustomConcern();
                            if (e.key === "Escape") { setShowAddConcern(false); setNewConcernInput(""); }
                          }}
                          placeholder="피부 고민 직접 입력"
                          maxLength={12}
                          className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-xs text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#84C13D] transition-all"
                        />
                        <button
                          onClick={addCustomConcern}
                          disabled={!newConcernInput.trim()}
                          className="px-3 py-2 rounded-xl text-xs font-semibold text-white disabled:opacity-50 transition-all"
                          style={{ background: "#84C13D" }}
                        >
                          추가
                        </button>
                        <button
                          onClick={() => { setShowAddConcern(false); setNewConcernInput(""); }}
                          className="px-3 py-2 rounded-xl text-xs font-medium bg-gray-100 text-gray-500 hover:bg-gray-200 transition-all"
                        >
                          취소
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* 가입 에러 메시지 */}
                {signupError && (
                  <div className="flex items-center gap-2 text-xs text-red-500 bg-red-50 border border-red-100 rounded-xl px-3 py-2.5">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    {signupError}
                  </div>
                )}

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
                    className="flex-1 py-3.5 rounded-xl text-sm font-semibold text-white transition-all cursor-pointer disabled:opacity-50"
                    style={step2Valid ? { background: "#84C13D", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" } : { background: "#D1D5DB" }}
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                      </span>
                    ) : "가입 완료"}
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
                  style={{ background: "#84C13D", boxShadow: "0 8px 24px rgba(133,193,61,0.4)" }}
                >
                  <Check className="w-10 h-10 text-white" />
                </motion.div>
                <h2 className="text-gray-900 font-bold mb-2">가입 완료!</h2>
                <p className="text-sm text-gray-500 mb-6">SKIN AI에 오신 것을 환영합니다 🌿<br />AI 피부 분석을 시작해 보세요!</p>
                <button
                  onClick={() => navigate("/chat")}
                  className="w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all cursor-pointer"
                  style={{ background: "#84C13D", boxShadow: "0 4px 14px rgba(133,193,61,0.35)" }}
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
