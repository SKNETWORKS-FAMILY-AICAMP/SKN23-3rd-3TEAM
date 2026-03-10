import { useState } from "react";
import * as authApi from "../api/authApi";
import { Link, useNavigate } from "react-router";
import { Alert } from "@/app/components/ui/alert";
import { Input } from "@/app/components/ui/input";
import { Button } from "@/app/components/ui/button";
import { motion, AnimatePresence } from "motion/react";
import LogoIdle from "@/assets/animations/logo_idle_1.webm";
import { Eye, EyeOff, Check, X, AlertCircle, Mail, Loader2 } from "lucide-react";

function PasswordStrength({ password }: { password: string }) {
    const checks = [
        { label: "8자 이상",    pass: password.length >= 8 },
        { label: "영문 포함",   pass: /[a-zA-Z]/.test(password) },
        { label: "숫자 포함",   pass: /[0-9]/.test(password) },
        { label: "특수문자 포함", pass: /[!@#$%^&*]/.test(password) },
    ];
    const strength = checks.filter((c) => c.pass).length;
    const strengthColor = ["", "#EF4444", "#F59E0B", "", "#10B981"];
    const strengthLabels = ["", "약함", "보통", "강함", "매우 강함"];

    return (
        <div className="mt-2">
            <div className="flex gap-1 mb-1.5">
                {[1, 2, 3, 4].map((i) => (
                    <div
                        key={i}
                        className={`flex-1 h-1.5 rounded-full transition-all duration-300 ${i <= strength && strength === 3 ? "bg-onyou" : ""}`}
                        style={{ background: i <= strength && strength !== 3 ? strengthColor[strength] : i > strength ? "#E5E7EB" : undefined }}
                    />
                ))}
            </div>
            <div className="flex items-center justify-between">
                <span className={`text-[11px] font-medium ${strength === 3 ? "text-onyou" : ""}`}
                    style={{ color: strength > 0 && strength !== 3 ? strengthColor[strength] : strength === 0 ? "#9CA3AF" : undefined }}>
                    {strength > 0 ? strengthLabels[strength] : "비밀번호를 입력하세요"}
                </span>
                <div className="flex gap-2.5">
                    {checks.map((c) => (
                        <div key={c.label} className={`flex items-center gap-1 text-[10px] ${c.pass ? "text-onyou" : "text-gray-300"}`}>
                            <Check className="w-2.5 h-2.5" />
                            {c.label}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export function SignupPage() {
    const navigate = useNavigate();

    // 계정 정보
    const [email, setEmail]               = useState("");
    const [emailVerified, setEmailVerified] = useState(false);
    const [emailSent, setEmailSent]       = useState(false);
    const [verifyCode, setVerifyCode]     = useState("");
    const [password, setPassword]         = useState("");
    const [passwordConfirm, setPasswordConfirm] = useState("");
    const [showConfirm, setShowConfirm]   = useState(false);
    const [name, setName]                 = useState("");
    const [nickname, setNickname]         = useState("");
    const [agreed] = useState(true);

    // 로딩 / 에러
    const [isSending, setIsSending]     = useState(false);
    const [isVerifying, setIsVerifying] = useState(false);
    const [isLoading, setIsLoading]     = useState(false);
    const [emailError, setEmailError]   = useState("");
    const [verifyError, setVerifyError] = useState("");
    const [signupError, setSignupError] = useState("");

    const isPasswordStrong = [
        password.length >= 8,
        /[a-zA-Z]/.test(password),
        /[0-9]/.test(password),
        /[!@#$%^&*]/.test(password),
    ].filter(Boolean).length >= 3;

    const passwordMatch = password === passwordConfirm && passwordConfirm.length > 0;

    const isValid =
        email.length > 0 &&
        emailVerified &&
        name.length > 0 &&
        isPasswordStrong &&
        passwordMatch &&
        agreed;

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

    /** 가입 완료 → 온보딩 이동 */
    const handleSignup = async () => {
        if (!isValid || isLoading) return;

        setIsLoading(true);
        setSignupError("");

        try {
            await authApi.signup({
                email,
                name,
                nickname         : nickname.trim() || name,
                password,
                terms_agreed     : agreed,
                privacy_agreed   : agreed,
                verification_code: verifyCode,
            });

            // 자동 로그인
            await authApi.login(email, password);

            // 신규 가입 → 온보딩으로 이동
            navigate("/onboarding", { replace: true });
        } catch (e) {
            const msg = e instanceof Error ? e.message : "가입에 실패했습니다. 다시 시도해 주세요.";

            // OTP 만료 에러 → 이메일 재인증 유도
            if (msg.includes("인증 코드")) {
                setEmailVerified(false);
                setEmailSent(false);
                setVerifyCode("");
                setVerifyError("");
                setEmailError("인증 코드가 만료되었습니다. 이메일 인증을 다시 진행해 주세요.");
            } else {
                setSignupError(msg);
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F8FBF3] flex items-center justify-center px-4 py-12">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-[440px]"
            >
                {/* 로고 */}
                <div className="text-center mb-7">
                    <p className="text-xl font-bold text-onyou"><b className="text-3xl mr-2">On_You</b>회원가입</p>
                    <div className="flex items-center justify-center mx-auto">
                        <video src={LogoIdle} autoPlay loop muted playsInline className="w-30 h-auto" />
                    </div>
                </div>

                <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-7">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key="signup-form"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-4"
                        >
                            <h2 className="text-gray-900 font-semibold mb-4 text-center">계정 정보 입력</h2>

                            {/* ── 이메일 ── */}
                            <div>
                                <div className="flex gap-2 items-end">
                                    <div className="flex-1">
                                        <Input
                                            label="이메일"
                                            required
                                            type="email"
                                            value={email}
                                            onChange={(e) => {
                                                setEmail(e.target.value);
                                                setEmailError("");

                                                if (emailVerified) {
                                                    setEmailVerified(false);
                                                    setEmailSent(false);
                                                }
                                            }}
                                            placeholder="이메일 주소"
                                            disabled={emailVerified}
                                            error={emailError}
                                        />
                                    </div>
                                    <button
                                        onClick={handleSendEmail}
                                        disabled={!email || emailVerified || isSending}
                                        className={`w-[80px] h-[45px] px-3 py-3 rounded-xl text-sm font-semibold text-white whitespace-nowrap cursor-pointer disabled:opacity-50 transition-all mb-[1px] ${emailVerified ? "bg-[#10B981]" : "bg-onyou"}`}
                                        style={{ minWidth: "80px" }}
                                    >
                                        {emailVerified ? (
                                            <span className="flex items-center gap-1"><Check className="w-3.5 h-3.5" />인증완료</span>
                                        ) : isSending ? (
                                            <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                                        ) : emailSent ? "재발송" : "인증발송"}
                                    </button>
                                </div>

                                {/* 코드 입력 영역 */}
                                {emailSent && !emailVerified && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: "auto" }}
                                        className="mt-2 overflow-hidden"
                                    >
                                        <div className="flex items-center gap-1.5 text-xs text-onyou mb-2 pl-1">
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
                                                className={`flex-1 px-4 py-3 border rounded-lg text-sm tracking-widest font-mono placeholder:font-sans placeholder:tracking-normal focus:outline-none transition-all ${
                                                    verifyError
                                                        ? "border-red-300 focus:border-red-400"
                                                        : "border-gray-200 focus:border-onyou"
                                                }`}
                                            />
                                            <button
                                                onClick={handleVerify}
                                                disabled={!verifyCode || isVerifying}
                                                className="w-[80px] h-[45px] px-4 py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-50 transition-all min-w-[52px] bg-onyou"
                                            >
                                                {isVerifying ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "확인"}
                                            </button>
                                        </div>

                                        {verifyError && (
                                            <p className="flex items-center gap-1 text-[11px] text-red-400 mt-1.5">
                                                <AlertCircle className="w-3 h-3 flex-shrink-0" />{verifyError}
                                            </p>
                                        )}

                                        <p className="text-xs text-gray-400 mt-1.5">
                                            코드가 오지 않으면{" "}
                                            <button
                                                onClick={handleSendEmail}
                                                disabled={isSending}
                                                className="text-onyou font-base mx-1 cursor-pointer hover:underline disabled:opacity-50"
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
                                <Input
                                    label="비밀번호"
                                    required
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="비밀번호"
                                />
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
                                        className={`w-full px-4 py-3 border rounded-lg text-sm text-gray-800 placeholder-gray-400 focus:outline-none transition-all pr-11 ${
                                            passwordConfirm
                                                ? passwordMatch
                                                    ? "border-onyou focus:border-onyou"
                                                    : "border-red-300 focus:border-red-400"
                                                : "border-gray-200 focus:border-onyou"
                                        }`}
                                    />
                                    <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 p-1 cursor-pointer">
                                        {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                    {passwordConfirm && (
                                        <div className="absolute right-9 top-1/2 -translate-y-1/2">
                                            {passwordMatch
                                                ? <Check className="w-4 h-4 text-onyou" />
                                                : <X className="w-4 h-4 text-red-400" />}
                                        </div>
                                    )}
                                </div>
                                {passwordConfirm && !passwordMatch && (
                                    <p className="text-[11px] text-red-400 mt-1">비밀번호가 일치하지 않습니다</p>
                                )}
                            </div>

                            {/* ── 이름 ── */}
                            <Input
                                label="이름"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="실명 입력"
                                maxLength={20}
                            />

                            {/* ── 닉네임 ── */}
                            <Input
                                label="닉네임"
                                value={nickname}
                                onChange={(e) => setNickname(e.target.value)}
                                placeholder="닉네임 (선택, 미입력 시 이름으로 설정)"
                                maxLength={12}
                            />


                            {/* 가입 에러 */}
                            {signupError && <Alert message={signupError} />}

                            {/* 가입 버튼 */}
                            <Button onClick={handleSignup} disabled={!isValid} isLoading={isLoading} loadingText="가입 중..." className="mt-2">
                                가입하기
                            </Button>
                        </motion.div>
                    </AnimatePresence>
                </div>

                <p className="text-xs text-center text-gray-400 mt-4">
                    이미 계정이 있으신가요?{" "}
                    <Link to="/login" className="font-medium hover:underline text-onyou">
                        로그인
                    </Link>
                </p>
            </motion.div>
        </div>
    );
}
