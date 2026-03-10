import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { Check, Plus, X, ArrowRight } from "lucide-react";
import LogoIdle from "@/assets/animations/logo_idle_1.webm";
import { fetchKeywords, updateCurrentUser, type KeywordItem } from "@/app/api/userApi";

const SKIN_TYPES = ["건성", "지성", "복합성", "중성", "민감성"];
const DEFAULT_CONCERNS = ["각질", "건조", "모공", "미백", "민감", "블랙헤드", "아토피", "유분", "장벽", "주름", "트러블", "피지", "흉터"];

export function OnboardingPage() {
    const navigate = useNavigate();
    const [gender, setGender] = useState("");
    const [age, setAge] = useState("");
    const [skinType, setSkinType] = useState("");
    const [selectedConcerns, setSelectedConcerns] = useState<string[]>([]);
    const [customConcerns, setCustomConcerns] = useState<string[]>([]);
    const [showAddConcern, setShowAddConcern] = useState(false);
    const [newConcernInput, setNewConcernInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [skinTypeKeywords, setSkinTypeKeywords] = useState<KeywordItem[]>([]);

    // 피부 타입 키워드 ID 매핑용 데이터 로드
    useEffect(() => {
        fetchKeywords("skin_type")
            .then(setSkinTypeKeywords)
            .catch(() => {}); // 실패해도 진행 가능
    }, []);

    const allConcerns = [...DEFAULT_CONCERNS, ...customConcerns];

    const isValid = gender !== "" && age !== "" && skinType !== "";

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

    const removeCustom = (c: string) => {
        setCustomConcerns((prev) => prev.filter((x) => x !== c));
        setSelectedConcerns((prev) => prev.filter((x) => x !== c));
    };

    const handleComplete = async () => {
        if (!isValid) return;
        setIsLoading(true);
        try {
            // 피부 타입 문자열 → keyword_id 매핑
            const skinTypeKeyword = skinTypeKeywords.find(
                (k) => k.label === skinType || k.keyword === skinType
            );

            await updateCurrentUser({
                gender      : gender === "여성" ? "female" : "male",
                age         : Number(age),
                skin_type   : skinTypeKeyword?.keyword_id ?? null,
                skin_concern: selectedConcerns.length > 0 ? selectedConcerns.join(",") : null,
            });
        } catch (err) {
            console.error("온보딩 저장 실패:", err);
            // 저장 실패해도 채팅으로 이동
        } finally {
            setIsLoading(false);
            navigate("/chat");
        }
    };

    return (
        <div className="min-h-screen bg-[#F8FBF3] flex items-center justify-center px-4 py-10">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="w-full max-w-[460px]"
            >
                <div className="flex items-center justify-center mx-auto mb-1">
                    <video src={LogoIdle} autoPlay loop muted playsInline className="w-24 h-auto" />
                </div>
                {/* Logo + Welcome */}
                <div className="text-center mb-8">
                    <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <h1 className="text-gray-900 font-bold mb-1">환영합니다!</h1>
                        <p className="text-sm text-gray-500 leading-relaxed">
                            맞춤 피부 분석을 위해 기본 정보를 설정해 주세요.<br />
                            나중에 설정에서 언제든 변경할 수 있어요.
                        </p>
                    </motion.div>
                </div>

                <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-7 space-y-6">
                    {/* Gender */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                    >
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-2.5">
                            성별 <span className="text-onyou">*</span>
                        </label>
                        <div className="flex gap-2">
                            {["여성", "남성"].map((g) => (
                                <button
                                    key={g}
                                    onClick={() => setGender(g)}
                                    className={`flex-1 py-3 rounded-xl text-sm font-medium border-2 transition-all duration-200 cursor-pointer ${
                                        gender === g ? "text-white border-transparent bg-onyou" : "border-gray-200 text-gray-600 hover:border-onyou"
                                    }`}
                                >
                                    {g}
                                </button>
                            ))}
                        </div>
                    </motion.div>

                    {/* Age */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-2.5">
                            나이 <span className="text-onyou">*</span>
                        </label>
                        <div className="relative">
                            <input
                                type="number"
                                value={age}
                                onChange={(e) => {
                                    const v = e.target.value;
                                    if (v === "" || (Number(v) >= 1 && Number(v) <= 120)) setAge(v);
                                }}
                                min={1}
                                max={120}
                                placeholder="나이를 입력하세요"
                                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-onyou focus:bg-white transition-all"
                            />
                        </div>
                    </motion.div>

                    {/* Divider */}
                    <div className="flex items-center gap-3">
                        <div className="flex-1 h-px bg-gray-100" />
                        <span className="text-xs text-gray-400 font-medium">피부 정보</span>
                        <div className="flex-1 h-px bg-gray-100" />
                    </div>

                    {/* Skin Type */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.25 }}
                    >
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-2.5">
                            피부 타입 <span className="text-onyou">*</span>
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {skinTypeKeywords.map((k) => {
                                const label = k.label ?? k.keyword;

                                return (
                                    <button
                                        key={k.keyword_id}
                                        onClick={() => setSkinType(label)}
                                        className={`px-3 py-2 rounded-xl text-xs font-medium border-2 transition-all duration-200 flex items-center gap-1.5 cursor-pointer ${
                                            skinType === label ? "text-white border-transparent bg-onyou" : "border-gray-200 text-gray-600 hover:border-onyou"
                                        }`}
                                    >
                                        {label}
                                    </button>
                                )
                            })}
                        </div>
                    </motion.div>

                    {/* Skin Concerns */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1">
                            피부 고민
                            <span className="ml-1.5 text-xxs font-normal text-gray-400 normal-case">(복수 선택 가능)</span>
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {allConcerns.map((c) => {
                                const selected = selectedConcerns.includes(c);
                                const isCustom = customConcerns.includes(c);
                                return (
                                    <button
                                        key={c}
                                        onClick={() => toggleConcern(c)}
                                        className={`px-3 py-2 rounded-xl text-xs font-medium border-2 transition-all flex items-center gap-1 cursor-pointer ${
                                            selected ? "text-white border-transparent bg-onyou" : "border-gray-200 text-gray-600 hover:border-onyou"
                                        }`}
                                    >
                                        {selected && <Check className="w-3 h-3" />}
                                        {c}
                                        {isCustom && (
                                            <X className="w-3 h-3 ml-0.5 opacity-70" onClick={(e) => { e.stopPropagation(); removeCustom(c); }} />
                                        )}
                                    </button>
                                );
                            })}

                            {!showAddConcern && (
                                <button
                                    onClick={() => setShowAddConcern(true)}
                                    className="px-3 py-2 rounded-xl text-xs font-medium border-2 border-dashed border-gray-300 text-gray-400 hover:border-onyou hover:text-onyou transition-all flex items-center gap-1 cursor-pointer"
                                >
                                    <Plus className="w-3.5 h-3.5" />
                                    직접 입력
                                </button>
                            )}
                        </div>

                        <AnimatePresence>
                            {showAddConcern && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="flex gap-2 mt-2"
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
                                        className="px-3 py-2 rounded-xl text-xs font-semibold text-white disabled:opacity-50 bg-onyou"
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
                    </motion.div>
                </div>

                {/* CTA */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="mt-5 space-y-3"
                >
                    <motion.button
                        onClick={handleComplete}
                        disabled={!isValid || isLoading}
                        whileTap={{ scale: 0.98 }}
                        className={`w-full py-4 rounded-2xl text-sm font-semibold text-white flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${isValid ? "bg-onyou" : "bg-[#D1D5DB]"}`}
                        style={isValid ? { boxShadow: "0 4px 20px rgba(133,193,61,0.4)" } : {}}
                    >
                        {isLoading ? (
                            <>
                                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                설정 중...
                            </>
                        ) : (
                            <>
                                시작하기
                                <ArrowRight className="w-4 h-4" />
                            </>
                        )}
                    </motion.button>

                    <button
                        onClick={() => navigate("/chat")}
                        className="w-full py-3 rounded-2xl text-sm font-medium text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
                    >
                        나중에 설정할게요
                    </button>
                </motion.div>
            </motion.div>
        </div>
    );
}
