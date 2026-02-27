import { Bot } from "@/app/components/ui/bot";
import { useLocation } from "react-router";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  X,
  Leaf,
  Send,
  ZoomIn,
  Sparkles,
  HelpCircle,
  ImagePlus,
  ChevronDown,
} from "lucide-react";

type AnalysisType = "default" | "quick" | "detailed" | "ingredient";

interface UploadSlot {
  id: string;
  label: string;
  tooltip: string;
  preview: string | null;
}

interface Message {
  id: number;
  role: "user" | "bot";
  content: string;
  image?: string;
  images?: string[];
  time: string;
}

// ─── Constants ────────────────────────────────────────────────────────
const ANALYSIS_OPTIONS = [
  { value: "default", label: "분석 선택" },
  { value: "quick", label: "빠른 분석" },
  { value: "detailed", label: "정밀 분석" },
  { value: "ingredient", label: "성분 분석" },
];

const ANALYSIS_HINTS: Record<string, string> = {
  quick: "얼굴 정면 1장으로 빠른 피부 상태 분석",
  detailed: "좌·정면·우측 3장으로 정밀 피부 분석",
  ingredient: "화장품 성분표 1장으로 성분 안전성 분석",
};

const INITIAL_MESSAGES: Message[] = [
  {
    id: 1,
    role: "bot",
    content: "안녕하세요! 저는 SKIN AI 피부 분석 챗봇이에요 🌿\n\n피부 이미지를 업로드하거나 피부 고민을 말씀해 주시면 맞춤형 분석과 제품을 추천해 드릴게요.",
    time: "오전 10:00",
  },
  {
    id: 2,
    role: "user",
    content: "제 피부가 요즘 너무 건조한데 어떤 보습제를 써야 할까요?",
    time: "오전 10:02",
  },
  {
    id: 3,
    role: "bot",
    content: "건조한 피부에는 세라마이드와 히알루론산이 함유된 보습제가 효과적이에요! 💧\n\n더 정확한 분석을 위해 피부 사진을 업로드해 주시면 피부 상태를 자세히 확인하고 맞춤 제품을 추천해 드릴게요. 아래 📎 버튼을 눌러 이미지를 업로드해 보세요.",
    time: "오전 10:02",
  },
  {
    id: 4,
    role: "user",
    content: "피부 분석 이미지를 업로드했어요",
    image: "https://images.unsplash.com/photo-1710301496719-11d44e51dbe3?w=300&h=300&fit=crop",
    time: "오전 10:04",
  },
  {
    id: 5,
    role: "bot",
    content: "이미지 분석이 완료되었어요! 🔍\n\n**분석 결과:**\n• 피부 타입: 수분 부족형 복합성 피부\n• T존 부위: 약간의 피지 분비\n• 볼 부위: 수분 부족, 건조함\n• 예상 수분도: 62/100\n• 예상 피지도: 74/100\n\n**추천 케어:**\n1. 세라마이드 함유 보습크림 (저자극)\n2. 히알루론산 에센스 레이어링\n3. 판테놀 성분 진정 토너\n\n자세한 분석 결과는 **분석 탭**에서 확인하실 수 있어요!",
    time: "오전 10:04",
  },
];

const getUploadSlots = (type: AnalysisType): UploadSlot[] => {
  switch (type) {
    case "quick":
      return [{ id: "front", label: "얼굴 정면", tooltip: "정면을 바라본 얼굴 사진을 업로드해 주세요. 밝은 자연광 아래에서 촬영하면 더 정확한 분석이 가능합니다.", preview: null }];
    case "detailed":
      return [
        { id: "left", label: "얼굴 좌측", tooltip: "왼쪽 45° 각도에서 촬영한 얼굴 사진을 업로드해 주세요. 귀가 보이도록 촬영하면 좋습니다.", preview: null },
        { id: "front", label: "얼굴 정면", tooltip: "정면을 바라본 얼굴 사진을 업로드해 주세요. 눈, 코, 입이 모두 보이도록 촬영해 주세요.", preview: null },
        { id: "right", label: "얼굴 우측", tooltip: "오른쪽 45° 각도에서 촬영한 얼굴 사진을 업로드해 주세요. 귀가 보이도록 촬영하면 좋습니다.", preview: null },
      ];
    case "ingredient":
      return [{ id: "label", label: "성분 표시면", tooltip: "화장품 뒷면의 전성분 표기란이 선명하게 보이도록 촬영해 주세요. 텍스트가 모두 보여야 정확한 분석이 가능합니다.", preview: null }];
    default:
      return [];
  }
};

// ─── EmptyChatState (chat_content=false 전용) ─────────────────────────
function EmptyChatState() {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 text-center">
      <motion.div
        className="relative mb-6"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "backOut" }}
      >
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ background: "rgba(133,193,61,0.12)" }}
          animate={{ scale: [1, 1.15, 1] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute inset-2 rounded-full"
          style={{ background: "rgba(133,193,61,0.2)" }}
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
        />
        <motion.div
          className="relative w-24 h-24 rounded-full flex items-center justify-center shadow-xl"
          style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)" }}
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        >
          <Leaf className="w-11 h-11 text-white" />
        </motion.div>
        {[
          { top: "-8px", right: "4px", delay: 0, size: 16 },
          { top: "4px", left: "-10px", delay: 0.6, size: 12 },
          { bottom: "-4px", right: "-4px", delay: 1.1, size: 14 },
        ].map((s, i) => (
          <motion.div
            key={i}
            className="absolute"
            style={{ top: s.top, right: s.right, left: s.left, bottom: s.bottom }}
            animate={{ opacity: [0.4, 1, 0.4], scale: [0.8, 1.2, 0.8] }}
            transition={{ duration: 2, repeat: Infinity, delay: s.delay }}
          >
            <Sparkles style={{ width: s.size, height: s.size, color: "#84C13D" }} />
          </motion.div>
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        <h2 className="font-bold text-gray-800 mb-2">SKIN AI와 대화를 시작하세요</h2>
        <p className="text-sm text-gray-500 mb-6 leading-relaxed max-w-xs">
          피부 고민을 입력하거나, 분석 유형을 선택하고<br />이미지를 업로드해 정밀 피부 분석을 받아보세요
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.5 }}
        className="flex flex-wrap justify-center gap-2"
      >
        {["피부 타입 알고 싶어요", "보습 크림 추천해줘", "여드름 케어 방법", "성분 분석 해줘"].map((q) => (
          <button
            key={q}
            className="px-4 py-2 rounded-full text-xs font-medium border-2 transition-all duration-200 hover:-translate-y-0.5"
            style={{ borderColor: "#84C13D", color: "#4A7A1E", background: "#F4FAE8" }}
          >
            {q}
          </button>
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="flex gap-1.5 mt-8"
      >
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: "#84C13D" }}
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3 }}
          />
        ))}
      </motion.div>
    </div>
  );
}

// ─── UploadSlotCard (chat_content=false 전용) ──────────────────────────
function UploadSlotCard({
  slot,
  onUpload,
  onRemove,
}: {
  slot: UploadSlot;
  onUpload: (id: string, file: File) => void;
  onRemove: (id: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="flex flex-col items-center gap-1.5 relative">
      <div
        className="relative w-full"
        onClick={() => !slot.preview && inputRef.current?.click()}
      >
        {slot.preview ? (
          <div className="relative w-full aspect-square rounded-xl overflow-hidden border-2 border-[#84C13D] cursor-pointer group">
            <img src={slot.preview} alt={slot.label} className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
              <button
                onClick={(e) => { e.stopPropagation(); onRemove(slot.id); }}
                className="opacity-0 group-hover:opacity-100 w-7 h-7 bg-white rounded-full flex items-center justify-center shadow-md transition-all"
              >
                <X className="w-3.5 h-3.5 text-gray-600" />
              </button>
            </div>
          </div>
        ) : (
          <div
            className="w-full aspect-square rounded-xl border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all hover:bg-[#F4FAE8]"
            style={{ borderColor: "#C5E89A" }}
          >
            <ImagePlus className="w-6 h-6 mb-1" style={{ color: "#84C13D" }} />
            <span className="text-[11px] font-medium" style={{ color: "#6BA32E" }}>업로드</span>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUpload(slot.id, file);
          }}
        />
      </div>

      <div className="flex items-center gap-1">
        <span className="text-[11px] font-medium text-gray-600">{slot.label}</span>
        <div className="relative">
          <button
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            className="text-gray-300 hover:text-[#84C13D] transition-colors"
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </button>
          <AnimatePresence>
            {showTooltip && (
              <motion.div
                initial={{ opacity: 0, y: 4, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 4, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-52 text-left"
              >
                <div className="bg-gray-800 text-white text-[11px] leading-relaxed rounded-xl px-3 py-2 shadow-xl">
                  {slot.tooltip}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent" style={{ borderTopColor: "#1F2937" }} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────
export function ChatPage() {
  const { state } = useLocation();
  const chat_content: boolean = state?.chat_content ?? false;

  // 공통 state
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [expandedImage, setExpandedImage] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // chat_content=false 전용 state
  const [analysisType, setAnalysisType] = useState<AnalysisType>("default");
  const [uploadSlots, setUploadSlots] = useState<UploadSlot[]>([]);
  const [analysisDropdownOpen, setAnalysisDropdownOpen] = useState(false);

  // chat_content=true 전용 state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMessages(chat_content ? INITIAL_MESSAGES : []);
  }, [chat_content]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    setUploadSlots(getUploadSlots(analysisType));
  }, [analysisType]);

  // ── Handlers (chat_content=false) ────────────────────────────────────
  const handleUpload = (slotId: string, file: File) => {
    const url = URL.createObjectURL(file);
    setUploadSlots((prev) =>
      prev.map((s) => s.id === slotId ? { ...s, preview: url } : s)
    );
  };

  const handleRemove = (slotId: string) => {
    setUploadSlots((prev) =>
      prev.map((s) => s.id === slotId ? { ...s, preview: null } : s)
    );
  };

  const canSend = (input.trim().length > 0 || uploadSlots.some((s) => s.preview)) && !isSending;

  const handleSend = async () => {
    if (chat_content) {
      if (!input.trim() || isSending) return;
      const userMsg: Message = {
        id: Date.now(),
        role: "user",
        content: input.trim(),
        time: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setIsSending(true);
      setTimeout(() => {
        const botMsg: Message = {
          id: Date.now() + 1,
          role: "bot",
          content: "네, 말씀하신 내용을 바탕으로 분석 중이에요 🌿\n\n피부 이미지를 함께 제공해 주시면 더 정확한 분석이 가능해요. 이미지 업로드 버튼을 클릭하거나 드래그 앤 드롭으로 이미지를 올려주세요!",
          time: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, botMsg]);
        setIsSending(false);
      }, 1500);
    } else {
      if (!canSend) return;
      const previews = uploadSlots.filter((s) => s.preview).map((s) => s.preview!);
      const userMsg: Message = {
        id: Date.now(),
        role: "user",
        content: input.trim() || `${ANALYSIS_OPTIONS.find(o => o.value === analysisType)?.label || "분석"} 요청`,
        images: previews.length > 0 ? previews : undefined,
        time: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setUploadSlots(getUploadSlots(analysisType));
      setAnalysisType("default");
      setIsSending(true);
      if (textareaRef.current) textareaRef.current.style.height = "auto";
      setTimeout(() => {
        const botResponses: Record<AnalysisType, string> = {
          quick: "이미지 분석이 완료되었어요! 🔍\n\n**빠른 분석 결과:**\n• 피부 타입: 수분 부족형 복합성 피부\n• T존: 약간의 피지 분비\n• 볼 부위: 수분 부족 감지\n• 종합 피부 점수: 69/100\n\n**추천 케어:**\n1. 세라마이드 보습크림 (저자극)\n2. 히알루론산 에센스 레이어링\n\n분석 탭에서 상세 결과를 확인하세요!",
          detailed: "정밀 분석이 완료되었어요! 🔬\n\n**정밀 분석 결과:**\n• 피부 타입: 수분 부족형 복합성 피부\n• 왼쪽: 건조, 모공 확대 소견\n• 정면: T존 피지 분비 활발\n• 오른쪽: 색소침착 소견\n\n3방향 이미지로 더 정확한 분석이 이루어졌어요. 분석 탭에서 상세 결과를 확인하세요!",
          ingredient: "성분 분석이 완료되었어요! 🧪\n\n**성분 안전성 결과:**\n• 등록된 성분 수: 24종\n• 안전 성분: 20종 ✅\n• 주의 성분: 3종 ⚠️\n• 위험 성분: 1종 ❌\n\n**주의 성분:** 파라벤류, 합성향료\n**특이 성분:** 레티놀 (임산부 주의)\n\n성분별 상세 설명은 분석 탭에서 확인하세요!",
          default: "네, 말씀하신 내용을 바탕으로 분석 중이에요 🌿\n\n피부 이미지를 함께 제공해 주시면 더 정확한 분석이 가능해요. 위의 분석 유형을 선택해 이미지를 업로드해 보세요!",
        };
        const botMsg: Message = {
          id: Date.now() + 1,
          role: "bot",
          content: botResponses[previews.length > 0 ? analysisType : "default"],
          time: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, botMsg]);
        setIsSending(false);
      }, 1800);
    }
  };

  // ── Handlers (chat_content=true) ──────────────────────────────────────
  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) handleImageUpload(file);
  };

  const handleImageUpload = (file: File) => {
    const url = URL.createObjectURL(file);
    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: "피부 이미지를 분석해 주세요",
      image: url,
      time: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setUploadModalOpen(false);
    setIsSending(true);
    setTimeout(() => {
      const botMsg: Message = {
        id: Date.now() + 1,
        role: "bot",
        content: "이미지를 분석하고 있어요... ✨\n\n분석이 완료되면 피부 상태와 맞춤 제품을 추천해 드릴게요!",
        time: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
      setIsSending(false);
    }, 2000);
  };

  // ── 공통 Handlers ─────────────────────────────────────────────────────
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const limit = chat_content ? 500 : 10000;
    if (e.target.value.length <= limit) {
      setInput(e.target.value);
      e.target.style.height = "auto";
      e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
    }
  };

  const formatContent = (content: string) => {
    return content.split("\n").map((line, i) => {
      const boldLine = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      return (
        <span key={i}>
          <span dangerouslySetInnerHTML={{ __html: boldLine }} />
          {i < content.split("\n").length - 1 && <br />}
        </span>
      );
    });
  };

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full bg-[#F8FBF3]">

      {/* Header */}
      {
        chat_content && (
          <div className="bg-white border-b border-gray-100 px-5 py-3.5 flex-shrink-0 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div>
                <h2 className="text-sm font-semibold text-gray-800" style={{textAlign: 'center'}}>AI 피부 분석 챗봇</h2>
              </div>
            </div>
          </div>
        )
      }

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {!chat_content && messages.length === 0 ? (
          <EmptyChatState />
        ) : (
          <div className="px-4 py-4 space-y-4">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} gap-3`}
                >
                  {msg.role === "bot" && (
                    <Bot />
                  )}
                  <div className={`max-w-[75%] flex flex-col gap-1 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                    {/* 단일 이미지 (chat_content=true) */}
                    {msg.image && (
                      <div
                        className="relative rounded-2xl overflow-hidden cursor-pointer group"
                        onClick={() => setExpandedImage(msg.image!)}
                      >
                        <img src={msg.image} alt="Uploaded" className="max-w-[200px] max-h-[200px] object-cover rounded-2xl" />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors rounded-2xl flex items-center justify-center">
                          <ZoomIn className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      </div>
                    )}
                    {/* 복수 이미지 (chat_content=false) */}
                    {msg.images && msg.images.length > 0 && (
                      <div className={`flex gap-2 ${msg.images.length > 1 ? "flex-row" : ""}`}>
                        {msg.images.map((img, idx) => (
                          <div
                            key={idx}
                            className="relative rounded-2xl overflow-hidden cursor-pointer group"
                            onClick={() => setExpandedImage(img)}
                          >
                            <img src={img} alt="Uploaded" className="max-w-[140px] max-h-[140px] object-cover rounded-2xl" />
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors rounded-2xl flex items-center justify-center">
                              <ZoomIn className="w-5 h-5 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <div
                      className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "text-white rounded-br-md"
                          : "text-gray-800 bg-white border border-gray-100 shadow-sm rounded-bl-md"
                      }`}
                      style={msg.role === "user" ? { background: "linear-gradient(135deg, #84C13D, #6BA32E)" } : {}}
                    >
                      {formatContent(msg.content)}
                    </div>
                    <span className="text-[10px] text-gray-400 px-1">{msg.time}</span>
                  </div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-xl bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1 overflow-hidden">
                      <img
                        src="https://images.unsplash.com/photo-1634469875582-a0885fc2f589?w=40&h=40&fit=crop"
                        alt="User"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {isSending && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-3"
              >
                <div
                  className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm"
                  style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)" }}
                >
                  <Leaf className="w-4 h-4 text-white" />
                </div>
                <div className="px-4 py-3 bg-white border border-gray-100 shadow-sm rounded-2xl rounded-bl-md flex items-center gap-1">
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 rounded-full bg-[#84C13D]"
                      animate={{ y: [0, -4, 0] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
                    />
                  ))}
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 이미지 업로드 슬롯 */}
      <AnimatePresence>
        {uploadSlots.length > 0 && (
          <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
              className="bg-white border-t border-gray-100 px-4 pt-3 pb-2 flex-shrink-0"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span
                    className="text-xs font-semibold px-2 py-0.5 rounded-lg text-white"
                    style={{ background: "#84C13D" }}
                  >
                    {ANALYSIS_OPTIONS.find((o) => o.value === analysisType)?.label}
                  </span>
                  <span className="text-[11px] text-gray-400">{ANALYSIS_HINTS[analysisType]}</span>
                </div>
                <span className="text-[11px] text-gray-400">
                  {uploadSlots.filter((s) => s.preview).length}/{uploadSlots.length} 업로드됨
                </span>
              </div>
              <div
                className={`grid gap-3 ${uploadSlots.length === 1 ? "grid-cols-1 max-w-[100px]" : uploadSlots.length === 3 ? "grid-cols-3 max-w-[320px]" : "grid-cols-2"}`}
              >
                {uploadSlots.map((slot) => (
                  <UploadSlotCard key={slot.id} slot={slot} onUpload={handleUpload} onRemove={handleRemove} />
                ))}
              </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-100 px-4 py-3 flex-shrink-0">
        <div className="flex items-end gap-2 bg-gray-50 rounded-2xl p-3 border-2 border-transparent focus-within:border-[#84C13D] transition-colors">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="피부 고민을 입력하세요..."
            className="flex-1 bg-transparent resize-none text-sm text-gray-800 placeholder-gray-400 outline-none max-h-[120px] leading-relaxed"
            rows={1}
          />

          {/* 분석 유형 선택 */}
          <div className="relative flex-shrink-0">
            <button
              onClick={() => setAnalysisDropdownOpen(!analysisDropdownOpen)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
                analysisType !== "default"
                  ? "border-[#84C13D] text-[#4A7A1E] bg-[#E8F5D0]"
                  : "border-gray-200 text-gray-500 bg-white hover:border-[#84C13D]"
              }`}
            >
              <span className="whitespace-nowrap">
                {ANALYSIS_OPTIONS.find((o) => o.value === analysisType)?.label}
              </span>
              <ChevronDown className="w-3 h-3" />
            </button>
            <AnimatePresence>
              {analysisDropdownOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 6, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 6, scale: 0.96 }}
                  transition={{ duration: 0.15 }}
                  className="absolute bottom-full right-0 mb-2 w-44 bg-white rounded-2xl shadow-xl border border-gray-100 z-50 overflow-hidden"
                >
                  {ANALYSIS_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => { setAnalysisType(opt.value as AnalysisType); setAnalysisDropdownOpen(false); }}
                      className={`w-full text-left px-4 py-2.5 text-xs font-medium transition-colors ${
                        analysisType === opt.value ? "bg-[#E8F5D0] text-[#4A7A1E]" : "text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      <span>{opt.label}</span>
                      {opt.value !== "default" && (
                        <p className="text-[10px] text-gray-400 mt-0.5">{ANALYSIS_HINTS[opt.value]}</p>
                      )}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {input.length > 100 && (
              <span className="text-[11px] text-gray-300">{input.length.toLocaleString()}/10,000</span>
            )}
            <motion.button
              onClick={handleSend}
              disabled={!canSend}
              whileTap={{ scale: 0.9 }}
              className="w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200"
              style={{
                background: canSend ? "linear-gradient(135deg, #84C13D, #6BA32E)" : "#E5E7EB",
              }}
            >
              <Send
                className="w-4 h-4"
                style={{ color: canSend ? "white" : "#9CA3AF" }}
              />
            </motion.button>
          </div>
        </div>
        <p className="text-[11px] text-gray-400 text-center mt-2">
          Enter 전송 · Shift+Enter 줄바꿈 · 최대 10,000자
        </p>
      </div>

      {/* 이미지 업로드 모달 (chat_content=true 전용) */}
      {chat_content && (
        <AnimatePresence>
          {uploadModalOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
              onClick={() => setUploadModalOpen(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ type: "spring", damping: 20 }}
                className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-8"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-semibold text-gray-800">이미지 업로드</h3>
                  <button
                    onClick={() => setUploadModalOpen(false)}
                    className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-500" />
                  </button>
                </div>
                <div
                  className="border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-colors"
                  style={{ borderColor: "#84C13D" }}
                  onDragOver={(e) => { e.preventDefault(); }}
                  onDrop={(e) => {
                    e.preventDefault();
                    const file = e.dataTransfer.files[0];
                    if (file) handleImageUpload(file);
                  }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
                    style={{ background: "#E8F5D0" }}
                  >
                    <ImagePlus className="w-7 h-7" style={{ color: "#84C13D" }} />
                  </div>
                  <p className="font-medium text-gray-700 mb-1">이미지를 드래그 앤 드롭하거나</p>
                  <p className="text-sm text-gray-400 mb-4">클릭하여 파일을 선택하세요</p>
                  <span
                    className="inline-block px-4 py-2 rounded-xl text-sm font-medium text-white"
                    style={{ background: "#84C13D" }}
                  >
                    파일 선택
                  </span>
                </div>
                <p className="text-[11px] text-gray-400 text-center mt-4">
                  JPG, PNG, WebP 형식 지원 • 최대 10MB
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleImageUpload(file);
                  }}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {/* 이미지 확대 모달 (공통) */}
      <AnimatePresence>
        {expandedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
            onClick={() => setExpandedImage(null)}
          >
            <button
              className="absolute top-4 right-4 w-10 h-10 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center transition-colors"
              onClick={() => setExpandedImage(null)}
            >
              <X className="w-5 h-5 text-white" />
            </button>
            <motion.img
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              src={expandedImage}
              alt="Expanded"
              className="max-w-[90vw] max-h-[90vh] object-contain rounded-2xl shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
