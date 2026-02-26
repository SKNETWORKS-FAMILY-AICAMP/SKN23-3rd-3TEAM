import { useState } from "react";
import {
  User,
  Lock,
  Link2,
  Check,
  ChevronRight,
  Eye,
  EyeOff,
  Loader2,
  Plus,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const SECTIONS = [
  { id: "profile", label: "프로필", icon: User },
  { id: "security", label: "보안", icon: Lock },
  { id: "social", label: "소셜 연동", icon: Link2 },
];

const SKIN_TYPES = ["건성", "지성", "복합성", "중성", "민감성"];
const DEFAULT_CONCERNS = ["수분 부족", "모공 케어", "미백", "탄력", "여드름", "색소침착", "홍조", "주름"];

export function SettingsPage() {
  const [activeSection, setActiveSection] = useState("profile");

  // Profile
  const [nickname, setNickname] = useState("김민지");
  const [age, setAge] = useState("26");
  const [gender, setGender] = useState("여성");
  const [skinType, setSkinType] = useState("복합성");
  const [selectedConcerns, setSelectedConcerns] = useState<string[]>(["수분 부족", "모공 케어"]);
  const [customConcerns, setCustomConcerns] = useState<string[]>([]);
  const [showAddConcern, setShowAddConcern] = useState(false);
  const [newConcernInput, setNewConcernInput] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Security
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");

  // Social
  const [socials, setSocials] = useState({ google: true, kakao: false, naver: true });

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

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((r) => setTimeout(r, 1800));
    setIsSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="h-full overflow-y-auto bg-[#F8FBF3]">
      <div className="max-w-4xl mx-auto px-4 py-6">
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
                return (
                  <button
                    key={s.id}
                    onClick={() => setActiveSection(s.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3.5 text-sm font-medium transition-all duration-200 ${
                      i < SECTIONS.length - 1 ? "border-b border-gray-50" : ""
                    } ${isActive ? "bg-[#E8F5D0] text-[#4A7A1E]" : "text-gray-600 hover:bg-gray-50"}`}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    {s.label}
                    {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto" style={{ color: "#85C13D" }} />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
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
                    <h3 className="font-semibold text-gray-800 mb-4 text-sm">기본 정보</h3>
                    <div className="flex items-center gap-4 mb-5 pb-5 border-b border-gray-50">
                      <div className="relative">
                        <img
                          src="https://images.unsplash.com/photo-1634469875582-a0885fc2f589?w=80&h=80&fit=crop"
                          alt="Profile"
                          className="w-16 h-16 rounded-2xl object-cover border-2"
                          style={{ borderColor: "#85C13D" }}
                        />
                        <button
                          className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-white text-xs shadow-sm"
                          style={{ background: "#85C13D" }}
                        >
                          +
                        </button>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400 mb-0.5">프로필 사진</p>
                        <button className="text-xs font-medium hover:underline" style={{ color: "#85C13D" }}>
                          사진 변경
                        </button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      {/* Read-only */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-xs font-medium text-gray-500 block mb-1.5">이름</label>
                          <div className="px-4 py-3 bg-gray-50 rounded-xl border border-gray-100 text-sm font-semibold text-gray-700">
                            김민지
                          </div>
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-500 block mb-1.5">이메일</label>
                          <div className="px-4 py-3 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-500 truncate">
                            minji@example.com
                          </div>
                        </div>
                      </div>

                      {/* Editable: nickname */}
                      <div>
                        <label className="text-xs font-medium text-gray-500 block mb-1.5">닉네임</label>
                        <input
                          value={nickname}
                          onChange={(e) => setNickname(e.target.value)}
                          className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 focus:outline-none focus:border-[#85C13D] transition-all"
                          maxLength={12}
                          placeholder="닉네임 입력"
                        />
                      </div>

                      {/* Gender + Age */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-xs font-medium text-gray-500 block mb-1.5">성별</label>
                          <select
                            value={gender}
                            onChange={(e) => setGender(e.target.value)}
                            className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 focus:outline-none focus:border-[#85C13D] transition-all appearance-none"
                          >
                            <option>여성</option>
                            <option>남성</option>
                            <option>선택 안함</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-500 block mb-1.5">나이</label>
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
                            className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 focus:outline-none focus:border-[#85C13D] transition-all"
                          />
                        </div>
                      </div>

                      {/* Divider */}
                      <div className="flex items-center gap-3 py-1">
                        <div className="flex-1 h-px bg-gray-100" />
                        <span className="text-[11px] text-gray-400 font-medium">피부 정보</span>
                        <div className="flex-1 h-px bg-gray-100" />
                      </div>

                      {/* Skin Type */}
                      <div>
                        <label className="text-xs font-medium text-gray-500 block mb-2">피부 타입</label>
                        <div className="flex flex-wrap gap-2">
                          {SKIN_TYPES.map((t) => (
                            <button
                              key={t}
                              onClick={() => setSkinType(t)}
                              className={`px-3 py-2 rounded-xl text-xs font-medium border-2 transition-all ${
                                skinType === t
                                  ? "text-white border-transparent"
                                  : "border-gray-200 text-gray-600 hover:border-[#85C13D]"
                              }`}
                              style={skinType === t ? { background: "#85C13D" } : {}}
                            >
                              {t}
                            </button>
                          ))}
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
                                className={`px-3 py-1.5 rounded-xl text-xs font-medium border-2 transition-all flex items-center gap-1.5 ${
                                  selected
                                    ? "border-transparent text-white"
                                    : "border-gray-200 text-gray-600 hover:border-[#85C13D]"
                                }`}
                                style={selected ? { background: "#85C13D" } : {}}
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

                          {/* '+' button */}
                          {!showAddConcern && (
                            <button
                              onClick={() => setShowAddConcern(true)}
                              className="px-3 py-1.5 rounded-xl text-xs font-medium border-2 border-dashed border-gray-300 text-gray-400 hover:border-[#85C13D] hover:text-[#85C13D] transition-all flex items-center gap-1"
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
                                className="flex-1 px-3 py-2 bg-white border border-gray-200 rounded-xl text-xs text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#85C13D] transition-all"
                              />
                              <button
                                onClick={addCustomConcern}
                                disabled={!newConcernInput.trim()}
                                className="px-3 py-2 rounded-xl text-xs font-semibold text-white disabled:opacity-50 transition-all"
                                style={{ background: "#85C13D" }}
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
                    <div className="max-w-4xl mx-auto">
                      <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="w-full py-3.5 rounded-2xl text-sm font-semibold text-white flex items-center justify-center gap-2 transition-all"
                        style={{
                          background: saved ? "#10B981" : "linear-gradient(135deg, #85C13D, #6BA32E)",
                          boxShadow: "0 4px 14px rgba(133,193,61,0.35)",
                        }}
                      >
                        {isSaving ? <><Loader2 className="w-4 h-4 animate-spin" />저장 중...</> :
                         saved ? <><Check className="w-4 h-4" />저장되었습니다!</> :
                         "변경사항 저장"}
                      </button>
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
                      <div>
                        <label className="text-xs font-medium text-gray-500 block mb-1.5">현재 비밀번호</label>
                        <div className="relative">
                          <input
                            type={showCurrentPw ? "text" : "password"}
                            value={currentPw}
                            onChange={(e) => setCurrentPw(e.target.value)}
                            placeholder="현재 비밀번호"
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:border-[#85C13D] transition-all pr-11"
                          />
                          <button onClick={() => setShowCurrentPw(!showCurrentPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 p-1">
                            {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 block mb-1.5">새 비밀번호</label>
                        <div className="relative">
                          <input
                            type={showNewPw ? "text" : "password"}
                            value={newPw}
                            onChange={(e) => setNewPw(e.target.value)}
                            placeholder="새 비밀번호 (8자 이상, 영문+숫자)"
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:border-[#85C13D] transition-all pr-11"
                          />
                          <button onClick={() => setShowNewPw(!showNewPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 p-1">
                            {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                    </div>
                    <button
                      className="w-full py-3 rounded-xl text-sm font-semibold text-white mt-4 transition-all disabled:opacity-50"
                      style={{ background: "linear-gradient(135deg, #85C13D, #6BA32E)" }}
                      disabled={!currentPw || !newPw}
                    >
                      비밀번호 변경
                    </button>
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
                    {[
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
                      {
                        id: "kakao", name: "카카오",
                        icon: <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#3C1E1E"><path d="M12 3C7.03 3 3 6.32 3 10.4c0 2.62 1.74 4.92 4.35 6.23l-.9 3.37 3.91-2.57C11.07 17.49 11.53 17.5 12 17.5c4.97 0 9-3.32 9-7.4S16.97 3 12 3z"/></svg>,
                        bg: "#FEE500",
                      },
                      {
                        id: "naver", name: "네이버",
                        icon: <span className="text-white font-black text-base">N</span>,
                        bg: "#03C75A",
                      },
                    ].map((social) => {
                      const connected = socials[social.id as keyof typeof socials];
                      return (
                        <div key={social.id} className="flex items-center justify-between px-5 py-4 border-b border-gray-50 last:border-0">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: social.bg }}>
                              {social.icon}
                            </div>
                            <div>
                              <p className="text-sm font-medium text-gray-800">{social.name}</p>
                              <p className="text-xs text-gray-400">{connected ? "연결됨" : "연결되지 않음"}</p>
                            </div>
                          </div>
                          <button
                            onClick={() => setSocials((prev) => ({ ...prev, [social.id]: !prev[social.id as keyof typeof socials] }))}
                            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                              connected ? "bg-gray-100 text-gray-500 hover:bg-red-50 hover:text-red-500" : "text-white"
                            }`}
                            style={!connected ? { background: "#85C13D" } : {}}
                          >
                            {connected ? "연결 해제" : "연결하기"}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
