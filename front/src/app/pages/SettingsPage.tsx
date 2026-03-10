import DefaultProfile from "@/assets/profile.png"
import { uploadImage } from "@/app/api/uploadApi";
import { Input } from "@/app/components/ui/input";
import { Button } from "@/app/components/ui/button";
import { useState, useEffect, useRef } from "react";
import { Loading } from "@/app/components/ui/loading";
import { motion, AnimatePresence } from "motion/react";
import { User, Link2, Check, ChevronRight, Loader2, Plus, X } from "lucide-react";
import { fetchCurrentUser, updateCurrentUser, fetchKeywords, fetchSocialLinks, KeywordItem } from "@/app/api/userApi";

const SECTIONS = [
    { id: "profile", label: "프로필", icon: User },
    { id: "social", label: "소셜 연동", icon: Link2 },
];

/** API 응답이 없을 때 사용할 피부 타입 폴백 목록 -> 필요한가..? */
const FALLBACK_SKIN_TYPES: KeywordItem[] = [
    { keyword_id: -1, type: "skin_type", keyword: "dry",       label: "건성",  description: null },
    { keyword_id: -2, type: "skin_type", keyword: "oily",      label: "지성",  description: null },
    { keyword_id: -3, type: "skin_type", keyword: "combo",     label: "복합성", description: null },
    { keyword_id: -4, type: "skin_type", keyword: "normal",    label: "중성",  description: null },
    { keyword_id: -5, type: "skin_type", keyword: "sensitive", label: "민감성", description: null },
];
const DEFAULT_CONCERNS = ["각질", "건조", "모공", "미백", "민감", "블랙헤드", "아토피", "유분", "장벽", "주름", "트러블", "피지", "흉터"];

/** back gender 값 → 화면 표시 레이블 */
const GENDER_LABEL: Record<string, string> = {
    male   : "남성",
    female : "여성",
};

export function SettingsPage() {
    const [activeSection, setActiveSection] = useState("profile");

    // 사용자 기본 정보 (read-only, API에서 로드)
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [profileImageUrl, setProfileImageUrl] = useState<string | null>(null);
    const [isLoadingUser, setIsLoadingUser] = useState(true);
    const [fetchError, setFetchError] = useState<string | null>(null);

    // Profile (editable)
    const [nickname, setNickname] = useState("");
    const [age, setAge] = useState("");
    const [gender, setGender] = useState("");
    const [skinType, setSkinType] = useState("");           // 선택된 label 문자열
    const [skinTypeKeywords, setSkinTypeKeywords] = useState<KeywordItem[]>(FALLBACK_SKIN_TYPES);
    const [selectedConcerns, setSelectedConcerns] = useState<string[]>([]);
    const [customConcerns, setCustomConcerns] = useState<string[]>([]);
    const [showAddConcern, setShowAddConcern] = useState(false);
    const [newConcernInput, setNewConcernInput] = useState("");
    const [isSaving, setIsSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);
    const profileInputRef = useRef<HTMLInputElement>(null);
    const [fieldErrors, setFieldErrors] = useState<{ gender?: string; age?: string; skinType?: string }>({});

    // ─── 사용자 정보 + skin_type 키워드 목록 동시 조회 ───
    useEffect(() => {
        setIsLoadingUser(true);

        Promise.all([fetchCurrentUser(), fetchKeywords("skin_type")])
            .then(([user, keywords]) => {
                // keywords 목록 설정 (빈 배열이면 폴백 유지)
                if (keywords.length > 0) setSkinTypeKeywords(keywords);

                setName(user.name);
                setEmail(user.email);
                setProfileImageUrl(user.profile_image_url ?? null);
                setNickname(user.nickname);
                setAge(user.age?.toString() ?? "");
                setGender(user.gender ? (GENDER_LABEL[user.gender] ?? "") : "");

                // skin_type (keyword_id) → label 변환
                const matched = keywords.find((k) => k.keyword_id === user.skin_type);

                setSkinType(matched?.label ?? "");

                if (user.skin_concern) {
                    const concerns = user.skin_concern.split(",").map((s) => s.trim()).filter(Boolean);
                    const customs = concerns.filter((c) => !DEFAULT_CONCERNS.includes(c));

                    setCustomConcerns(customs);
                    setSelectedConcerns(concerns);
                }
            })
            .catch((err: Error) => setFetchError(err.message))
            .finally(() => setIsLoadingUser(false));
    }, []);

    // 소셜 탭 진입 시 1회 조회
    useEffect(() => {
        if (activeSection !== "social" || socialFetchedRef.current) return;

        socialFetchedRef.current = true;
        
        setIsLoadingSocials(true);
        fetchSocialLinks()
            .then((data) => setConnectedProviders(data.providers))
            .catch((err: Error) => console.error("소셜 연동 조회 실패:", err))
            .finally(() => setIsLoadingSocials(false));
    }, [activeSection]);

    // Security
    const [currentPw, setCurrentPw]           = useState("");
    const [newPw, setNewPw]                   = useState("");
    const [confirmPw, setConfirmPw]           = useState("");

    const pwMatch = confirmPw.length > 0 && newPw === confirmPw;

    // Social
    const [connectedProviders, setConnectedProviders] = useState<string[]>([]);
    const [isLoadingSocials, setIsLoadingSocials] = useState(false);
    const socialFetchedRef = useRef(false);

    const allConcerns = [...DEFAULT_CONCERNS, ...customConcerns];

    const toggleConcern = (c: string) => {
        setSelectedConcerns((prev) =>
            prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
        );
    };

    const addCustomConcern = () => {
        const trimmed = newConcernInput.trim();
        if (trimmed && !allConcerns.includes(trimmed)) {
            setCustomConcerns((prev) => [...prev, trimmed]);
            setSelectedConcerns((prev) => [...prev, trimmed]);
        }
        setNewConcernInput("");
        setShowAddConcern(false);
    };

    const removeConcern = (c: string) => {
        setCustomConcerns((prev) => prev.filter((x) => x !== c));
        setSelectedConcerns((prev) => prev.filter((x) => x !== c));
    };

    const GENDER_TO_API: Record<string, "male" | "female"> = {
        "여성": "female",
        "남성": "male",
    };

    const handlePhotoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];

        if (!file) return;

        setIsUploadingPhoto(true);

        try {
            const url = await uploadImage(file, "profile");
            // S3에 고정 파일명(profile.ext)으로 덮어쓰므로 URL이 동일함
            // 타임스탬프 쿼리스트링을 붙여 브라우저 캐시를 무효화
            setProfileImageUrl(`${url}?t=${Date.now()}`);
        } catch (err) {
            console.error("프로필 사진 업로드 실패:", err);
        } finally {
            setIsUploadingPhoto(false);
            // 같은 파일 재선택 허용
            if (profileInputRef.current) profileInputRef.current.value = "";
        }
    };

    const handleSave = async () => {
        // 필수 필드 검증
        const errors: { gender?: string; age?: string; skinType?: string } = {};

        if (!gender) errors.gender = "성별을 선택해 주세요.";
        if (!age)                             errors.age     = "나이를 입력해 주세요.";
        if (!skinType)                        errors.skinType = "피부 타입을 선택해 주세요.";
        if (Object.keys(errors).length > 0) {
            setFieldErrors(errors);

            return;
        }

        setFieldErrors({});
        setIsSaving(true);
        setSaveError(null);

        try {
            const skinKeywordId = skinTypeKeywords.find((k) => k.label === skinType)?.keyword_id ?? null;

            await updateCurrentUser({
                nickname,
                age              : age ? Number(age) : null,
                gender           : GENDER_TO_API[gender],
                skin_type        : skinKeywordId,
                skin_concern     : selectedConcerns.length > 0 ? selectedConcerns.join(",") : null,
                profile_image_url: profileImageUrl,
            });

            // 사이드바 프로필 이미지 갱신 알림
            window.dispatchEvent(new CustomEvent("profileUpdated"));

            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (err) {
            setSaveError(err instanceof Error ? err.message : "저장에 실패했습니다.");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="h-full overflow-y-auto bg-[#F8FBF3]">
            <div className="max-w-5xl mx-auto px-4 py-6">
                {/* Header */}
                <div className="mb-6">
                    <h1 className="text-gray-900 font-bold">설정 · 마이페이지</h1>
                    <p className="text-sm text-gray-500 mt-0.5">계정 정보와 환경 설정을 관리하세요</p>
                </div>

                <div className="flex flex-col md:flex-row gap-5">
                    {/* Side Menu */}
                    <div className="md:w-52 flex-shrink-0">
                        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                            {SECTIONS.map((s, i) => {
                                const Icon = s.icon;
                                const isActive = activeSection === s.id;
                                const isDisabled = s.id === "security";

                                return (
                                    <button
                                        key={s.id}
                                        onClick={() => !isDisabled && setActiveSection(s.id)}
                                        disabled={isDisabled}
                                        className={`w-full flex items-center gap-3 px-4 py-3.5 text-sm font-medium transition-all duration-200 ${
                                            i < SECTIONS.length - 1 ? "border-b border-gray-50" : ""
                                        } ${isDisabled ? "opacity-35 cursor-not-allowed" : "cursor-pointer"} ${
                                            isActive ? "bg-[#E8F5D0] text-[#4A7A1E]" : "text-gray-600 hover:bg-gray-50"
                                        }`}
                                    >
                                        <Icon className="w-4 h-4 flex-shrink-0" />
                                        {s.label}
                                        {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto text-onyou" />}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    <div className="flex-1 min-w-0">
                        {isLoadingUser ? (
                            <Loading />
                        ) : fetchError ? (
                            <div className="py-4 text-center text-sm text-red-500">{fetchError}</div>
                        ) : (
                            <AnimatePresence mode="wait">
                                {/* ── Profile ── */}
                                {activeSection === "profile" && (
                                    <motion.div
                                        key="profile"
                                        initial={{ opacity: 0, x: 10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -10 }}
                                        className="space-y-5 pb-24"
                                    >
                                        {/* Photo + read-only info */}
                                        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                                            <h3 className="font-semibold text-gray-800 mb-4 text-sm">프로필</h3>
                                            <div className="flex items-start gap-1 mb-5">
                                                <div className="flex flex-col gap-1.5 items-center relative text-center">
                                                    {isUploadingPhoto ? (
                                                        <div className="w-16 h-16 rounded-2xl border-2 border-onyou flex items-center justify-center bg-gray-50">
                                                            <Loader2 className="w-5 h-5 animate-spin text-onyou" />
                                                        </div>
                                                    ) : (
                                                        <img
                                                            src={profileImageUrl ?? DefaultProfile}
                                                            alt="Profile"
                                                            className="w-20 h-20 rounded-2xl object-cover border-2 border-onyou"
                                                        />
                                                    )}
                                                    <input ref={profileInputRef} type="file" accept="image/*" className="hidden" onChange={handlePhotoChange} />
                                                    <button
                                                        onClick={() => profileInputRef.current?.click()}
                                                        disabled={isUploadingPhoto}
                                                        className="text-xs font-medium text-onyou cursor-pointer hover:underline disabled:opacity-50 block"
                                                    >
                                                        사진 변경
                                                    </button>
                                                </div>
                                                
                                                {/* Read-only */}
                                                <div className="flex flex-col gap-2.5 mt-3">
                                                    <div className="grid grid-cols-3 gap-3">
                                                        <label className="text-sm font-medium text-gray-500 text-right block">이름</label>
                                                        <p className="col-span-2 text-sm font-medium text-gray-600">{name}</p>
                                                    </div>
                                                    <div className="grid grid-cols-3 gap-3">
                                                        <label className="text-sm font-medium text-gray-500 text-right block">이메일</label>
                                                        <p className="col-span-2 text-sm font-medium text-gray-600">{email}</p>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Editable */}
                                            <div className="space-y-4">
                                                {/* Divider */}
                                                <div className="flex items-center gap-3 py-1">
                                                    <div className="flex-1 h-px bg-gray-100" />
                                                    <span className="text-xs text-gray-400 font-medium">기본 정보</span>
                                                    <div className="flex-1 h-px bg-gray-100" />
                                                </div>

                                                {/* nickname */}
                                                <Input
                                                    label="닉네임"
                                                    value={nickname}
                                                    onChange={(e) => setNickname(e.target.value)}
                                                    maxLength={12}
                                                    placeholder="닉네임 입력"
                                                />

                                                {/* Gender + Age */}
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div>
                                                        <label className="text-xs font-medium text-gray-500 block mb-1.5">성별 <span className="text-red-400">*</span></label>
                                                        <select
                                                            value={gender}
                                                            onChange={(e) => { setGender(e.target.value); setFieldErrors((p) => ({ ...p, gender: undefined })); }}
                                                            className={`w-full px-4 py-3 bg-white border rounded-xl text-sm text-gray-800 cursor-pointer focus:outline-none transition-all appearance-none ${fieldErrors.gender ? "border-red-400 focus:border-red-400" : "border-gray-200 focus:border-onyou"}`}
                                                        >
                                                            <option value="" disabled>성별 선택</option>
                                                            <option>여성</option>
                                                            <option>남성</option>
                                                        </select>
                                                        {fieldErrors.gender && <p className="text-xs text-red-500 mt-1">{fieldErrors.gender}</p>}
                                                    </div>
                                                    <Input
                                                        label="나이"
                                                        required
                                                        type="number"
                                                        value={age}
                                                        onChange={(e) => {
                                                            const v = e.target.value;
                                                            if (v === "" || (Number(v) >= 1 && Number(v) <= 120)) setAge(v);
                                                            setFieldErrors((p) => ({ ...p, age: undefined }));
                                                        }}
                                                        min={1}
                                                        max={120}
                                                        placeholder="나이 입력"
                                                        error={fieldErrors.age}
                                                    />
                                                </div>

                                                {/* Divider */}
                                                <div className="flex items-center gap-3 mt-7 py-1">
                                                    <div className="flex-1 h-px bg-gray-100" />
                                                    <span className="text-xs text-gray-400 font-medium">피부 정보</span>
                                                    <div className="flex-1 h-px bg-gray-100" />
                                                </div>

                                                {/* Skin Type */}
                                                <div>
                                                    <label className={`text-xs font-medium block mb-2 ${fieldErrors.skinType ? "text-red-500" : "text-gray-500"}`}>
                                                        피부 타입 <span className="text-red-400">*</span>{fieldErrors.skinType && <span className="font-normal"> — {fieldErrors.skinType}</span>}
                                                    </label>
                                                    <div className="flex flex-wrap gap-2">
                                                        {skinTypeKeywords.map((k) => {
                                                            const label = k.label ?? k.keyword;

                                                            return (
                                                                <button
                                                                    key={k.keyword_id}
                                                                    onClick={() => { setSkinType(label); setFieldErrors((p) => ({ ...p, skinType: undefined })); }}
                                                                    className={`px-3 py-2 rounded-xl text-xs font-medium border-2 transition-all cursor-pointer ${
                                                                        skinType === label
                                                                            ? "text-white border-transparent bg-onyou"
                                                                            : fieldErrors.skinType
                                                                                ? "border-red-200 text-gray-600 hover:border-red-400"
                                                                                : "border-gray-200 text-gray-600 hover:border-onyou"
                                                                    }`}
                                                                >
                                                                    {label}
                                                                </button>
                                                            );
                                                        })}
                                                    </div>
                                                </div>

                                                {/* Skin Concerns */}
                                                <div>
                                                    <label className="text-xs font-medium text-gray-500 block mb-2">피부 고민</label>
                                                    <div className="flex flex-wrap gap-2">
                                                        {allConcerns.map((c) => {
                                                            const selected = selectedConcerns.includes(c);
                                                            const isCustom = customConcerns.includes(c);

                                                            return (
                                                                <button
                                                                    key={c}
                                                                    onClick={() => toggleConcern(c)}
                                                                    className={`px-3 py-1.5 rounded-xl text-xs font-medium border-2 transition-all flex items-center gap-1.5 cursor-pointer ${
                                                                        selected
                                                                            ? "border-transparent text-white bg-onyou"
                                                                            : "border-gray-200 text-gray-600 hover:border-onyou"
                                                                    }`}
                                                                >
                                                                    {selected && <Check className="w-3 h-3 flex-shrink-0" />}
                                                                    {c}
                                                                    {isCustom && (
                                                                        <span className="ml-0.5" onClick={(e) => { e.stopPropagation(); removeConcern(c); }}>
                                                                            <X className="w-3 h-3" />
                                                                        </span>
                                                                    )}
                                                                </button>
                                                            );
                                                        })}

                                                        {/* '+' button */}
                                                        {!showAddConcern && (
                                                            <button
                                                                onClick={() => setShowAddConcern(true)}
                                                                className="px-3 py-1.5 rounded-xl text-xs font-medium border-2 border-dashed border-gray-300 text-gray-400 cursor-pointer hover:border-onyou hover:text-onyou transition-all flex items-center gap-1"
                                                            >
                                                                <Plus className="w-3.5 h-3.5" />
                                                                추가
                                                            </button>
                                                        )}
                                                    </div>

                                                    {/* Custom concern input */}
                                                    <AnimatePresence>
                                                        {showAddConcern && (
                                                            <motion.div
                                                                initial={{ opacity: 0, height: 0 }}
                                                                animate={{ opacity: 1, height: "auto" }}
                                                                exit={{ opacity: 0, height: 0 }}
                                                                className="mt-2 flex gap-2"
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
                                                                    className="flex-1 px-3 py-2 bg-white border border-gray-200 rounded-xl text-xs text-gray-800 placeholder-gray-400 focus:outline-none focus:border-onyou transition-all"
                                                                />
                                                                <button
                                                                    onClick={addCustomConcern}
                                                                    disabled={!newConcernInput.trim()}
                                                                    className="px-3 py-2 rounded-xl text-xs font-semibold text-white disabled:opacity-50 transition-all bg-onyou"
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
                                            </div>
                                        </div>

                                        {/* Save Button - fixed bottom */}
                                        <div className="fixed bottom-0 left-0 right-0 lg:left-[260px] bg-white border-t border-gray-100 px-4 py-4 z-20">
                                            <div className="max-w-4xl mx-auto space-y-2">
                                                {saveError && (
                                                    <p className="text-xs text-red-500 text-center">{saveError}</p>
                                                )}
                                                <Button
                                                    onClick={handleSave}
                                                    disabled={isUploadingPhoto}
                                                    isLoading={isSaving}
                                                    loadingText="저장 중..."
                                                    className="rounded-2xl"
                                                >
                                                    {saved ? <><Check className="w-4 h-4" />저장되었습니다!</> : "변경사항 저장"}
                                                </Button>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}

                                {/* ── Security ── */}
                                {activeSection === "security" && (
                                    <motion.div
                                        key="security"
                                        initial={{ opacity: 0, x: 10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -10 }}
                                    >
                                        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                                            <h3 className="font-semibold text-gray-800 mb-4 text-sm">비밀번호 변경</h3>
                                            <div className="space-y-3">
                                                <Input
                                                    label="현재 비밀번호"
                                                    type="password"
                                                    value={currentPw}
                                                    onChange={(e) => setCurrentPw(e.target.value)}
                                                    placeholder="현재 비밀번호"
                                                />
                                                <Input
                                                    label="새 비밀번호"
                                                    type="password"
                                                    value={newPw}
                                                    onChange={(e) => setNewPw(e.target.value)}
                                                    placeholder="새 비밀번호 (8자 이상, 영문+숫자)"
                                                />
                                                <Input
                                                    label="비밀번호 확인"
                                                    type="password"
                                                    value={confirmPw}
                                                    onChange={(e) => setConfirmPw(e.target.value)}
                                                    placeholder="새 비밀번호를 다시 입력하세요"
                                                    error={confirmPw.length > 0 && !pwMatch ? "비밀번호가 일치하지 않습니다" : undefined}
                                                />
                                            </div>
                                            <Button disabled={!currentPw || !newPw || !pwMatch} className="mt-4">
                                                비밀번호 변경
                                            </Button>
                                        </div>
                                    </motion.div>
                                )}

                                {/* ── Social ── */}
                                {activeSection === "social" && (
                                    <motion.div
                                        key="social"
                                        initial={{ opacity: 0, x: 10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -10 }}
                                    >
                                        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                                            <div className="px-5 py-4 border-b border-gray-50">
                                                <h3 className="font-semibold text-gray-800 text-sm">소셜 계정 연동</h3>
                                                <p className="text-xs text-gray-400 mt-0.5">연결된 소셜 계정으로 간편 로그인이 가능합니다</p>
                                            </div>
                                            {isLoadingSocials ? (
                                                <div className="flex items-center justify-center py-10">
                                                    <Loader2 className="w-5 h-5 animate-spin text-onyou" />
                                                </div>
                                            ) : (
                                                [
                                                    {
                                                        id: "google", name: "Google",
                                                        icon: (
                                                            <svg className="w-5 h-5" viewBox="0 0 24 24">
                                                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                                            </svg>
                                                        ),
                                                        bg: "#F3F4F6",
                                                    },
                                                    // {
                                                    //   id: "kakao", name: "카카오",
                                                    //   icon: <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#3C1E1E"><path d="M12 3C7.03 3 3 6.32 3 10.4c0 2.62 1.74 4.92 4.35 6.23l-.9 3.37 3.91-2.57C11.07 17.49 11.53 17.5 12 17.5c4.97 0 9-3.32 9-7.4S16.97 3 12 3z"/></svg>,
                                                    //   bg: "#FEE500",
                                                    // },
                                                    {
                                                        id: "naver", name: "네이버",
                                                        icon: <span className="text-white font-black text-base">N</span>,
                                                        bg: "#03C75A",
                                                    },
                                                ].map((social) => {
                                                    const connected = connectedProviders.includes(social.id);
                                                    return (
                                                        <div key={social.id} className="flex items-center px-5 py-4 border-b border-gray-50 last:border-0">
                                                            <div className="flex items-center gap-3">
                                                                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: social.bg }}>
                                                                    {social.icon}
                                                                </div>
                                                                <div>
                                                                    <p className="text-sm font-medium text-gray-800">{social.name}</p>
                                                                    <p className={`text-xs font-medium mt-0.5 ${connected ? "text-onyou" : "text-gray-400"}`}>
                                                                        {connected ? "연결됨" : "연결되지 않음"}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                            {connected && (
                                                                <Check className="w-4 h-4 ml-auto text-onyou" />
                                                            )}
                                                        </div>
                                                    );
                                                })
                                            )}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
