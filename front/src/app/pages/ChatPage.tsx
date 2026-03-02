import { useLocation, Link } from "react-router";
import { Bot } from "@/app/components/ui/bot";
import defaultProfile from "@/assets/profile.png"
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import logoTextWebm from "@/assets/animations/logo_text.webm";
import loadingWebm from "@/assets/animations/logo_loop_1.webm";
import infoImg1 from "@/assets/info_1.png";
import infoImg2 from "@/assets/info_2.png";
import ReactMarkdown from 'react-markdown'
import {
  X,
  Send,
  ZoomIn,
  Sparkles,
  HelpCircle,
  ImagePlus,
  ChevronDown,
  Lock,
} from "lucide-react";
import {
  createChatRoom,
  fetchMessages,
  sendMessage,
  sendGuestMessage,
  type ChatMessage,
} from "@/app/api/chatApi";
import { uploadImage } from "@/app/api/uploadApi";
import { Icon } from "@/app/components/ui/icon";

type AnalysisType = "default" | "simple" | "detailed" | "ingredient";

interface UploadSlot {
  id      : string;
  label   : string;
  tooltip : string;
  preview : string | null;  // blob URL (미리보기용)
  file    : File   | null;  // 실제 파일 (S3 업로드용)
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
  { value: "simple", label: "빠른 분석" },
  { value: "detailed", label: "정밀 분석" },
  { value: "ingredient", label: "성분 분석" },
];

const ANALYSIS_HINTS: Record<string, string> = {
  simple: "얼굴 정면 1장으로 빠른 피부 상태 분석",
  detailed: "좌·정면·우측 3장으로 정밀 피부 분석",
  ingredient: "화장품 성분표 1장으로 성분 안전성 분석",
};

const getUploadSlots = (type: AnalysisType): UploadSlot[] => {
  switch (type) {
    case "simple":
      return [{ id: "front", label: "얼굴 정면", tooltip: "정면을 바라본 얼굴 사진을 업로드해 주세요. 밝은 자연광 아래에서 촬영하면 더 정확한 분석이 가능합니다.", preview: null, file: null }];
    case "detailed":
      return [
        { id: "front", label: "얼굴 정면", tooltip: "정면을 바라본 얼굴 사진을 업로드해 주세요. 눈, 코, 입이 모두 보이도록 촬영해 주세요.",  preview: null, file: null },
        { id: "left",  label: "얼굴 좌측", tooltip: "왼쪽 45° 각도에서 촬영한 얼굴 사진을 업로드해 주세요. 귀가 보이도록 촬영하면 좋습니다.", preview: null, file: null },
        { id: "right", label: "얼굴 우측", tooltip: "오른쪽 45° 각도에서 촬영한 얼굴 사진을 업로드해 주세요. 귀가 보이도록 촬영하면 좋습니다.", preview: null, file: null },
      ];
    case "ingredient":
      return [{ id: "label", label: "성분 표시면", tooltip: "화장품 뒷면의 전성분 표기란이 선명하게 보이도록 촬영해 주세요. 텍스트가 모두 보여야 정확한 분석이 가능합니다.", preview: null, file: null }];
    default:
      return [];
  }
};

// ─── image_url 파싱 ───────────────────────────────────────────────────
// DB에서 split(",")으로 저장된 경우 각 요소에 ["  "  "] 같은 문자가 포함됨
// regex로 실제 URL만 추출
function parseImageUrls(raw: string[] | string | null): string[] {
  if (!raw) return [];

  const arr = Array.isArray(raw) ? raw : [raw];

  return arr
    .map((item) => {
      const match = item.match(/https?:\/\/[^\s"'\[\]]+/);
      return match ? match[0] : null;
    })
    .filter(Boolean) as string[];
}

// ─── API 메시지 → UI 메시지 변환 ─────────────────────────────────────
function apiMsgToMessage(msg: ChatMessage): Message {
  const urls   = parseImageUrls(msg.image_url);
  const images = urls.length > 0 ? urls : undefined;
  return {
    id     : msg.message_id,
    role   : msg.role === "assistant" ? "bot" : "user",
    content: msg.content,
    image  : images?.length === 1 ? images[0] : undefined,
    images : images && images.length > 1 ? images : undefined,
    time   : new Date(msg.created_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
  };
}

// ─── EmptyChatState (새 채팅 전용) ────────────────────────────────────
function EmptyChatState() {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 text-center">
      <motion.div
        className="relative mb-6"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "backOut" }}
      >
        <h2 className="font-bold text-[22px] text-[#84C13D] ">내 피부를 위한 AI 도우미</h2>
      </motion.div>
      <motion.div
        className="relative mb-6"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "backOut" }}
      >
        <video src={logoTextWebm} autoPlay loop muted playsInline className="w-70 h-auto" />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
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
    </div>
  );
}

// ─── UploadSlotCard ──────────────────────────
function UploadSlotCard({ slot, onUpload, onRemove }: {
  slot: UploadSlot;
  onUpload: (id: string, file: File) => void;
  onRemove: (id: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex flex-col items-center gap-1.5 relative">
      <div
        className="relative w-full"
        onClick={() => !slot.preview && inputRef.current?.click()}
      >
        {slot.preview ? (
          <div className="relative w-full aspect-square rounded-lg overflow-hidden border-2 border-[#84C13D] cursor-pointer group">
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
      </div>
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────
export function ChatPage() {
  const { state } = useLocation();

  // state.chat_room_id가 있으면 기존 채팅, 없으면 새 채팅
  const chat_content: boolean = !!(state?.chat_room_id);
  const [chatRoomId, setChatRoomId] = useState<number | null>(state?.chat_room_id ?? null);

  // 공통 state
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [expandedImage, setExpandedImage] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const skipFetchRef = useRef(false); // 새 채팅방 생성 시 불필요한 fetchMessages 방지

  const isLoggedIn = !!localStorage.getItem("access_token");

  // 새 채팅 전용 state
  const [analysisType, setAnalysisType] = useState<AnalysisType>("default");
  const [uploadSlots, setUploadSlots] = useState<UploadSlot[]>([]);
  const [analysisDropdownOpen, setAnalysisDropdownOpen] = useState(false);
  const [showAnalysisToast, setShowAnalysisToast] = useState(false);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const triggerAnalysisToast = () => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setShowAnalysisToast(true);
    toastTimerRef.current = setTimeout(() => setShowAnalysisToast(false), 3000);
  };

  // 기존 채팅 전용 state
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 다른 채팅방 클릭 시 chatRoomId 업데이트
  useEffect(() => {
    const newId = state?.chat_room_id ?? null;
    setChatRoomId(newId);
  }, [state?.chat_room_id]);

  // chatRoomId가 있으면 메시지 내역 조회
  useEffect(() => {
    if (chatRoomId === null) {
      setMessages([]);
      return;
    }
    // 새 채팅방 생성 직후(handleSend 중)에는 fetch 건너뜀
    if (skipFetchRef.current) {
      skipFetchRef.current = false;
      return;
    }
    setIsLoadingHistory(true);
    fetchMessages(chatRoomId)
      .then((msgs) => setMessages(msgs.map(apiMsgToMessage)))
      .catch((err: Error) => console.error("채팅 내역 조회 실패:", err))
      .finally(() => setIsLoadingHistory(false));
  }, [chatRoomId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    setUploadSlots(getUploadSlots(analysisType));
  }, [analysisType]);

  // ── Handlers (새 채팅 - 이미지 업로드 슬롯) ──────────────────────────
  const handleUpload = (slotId: string, file: File) => {
    const url = URL.createObjectURL(file);
    setUploadSlots((prev) =>
      prev.map((s) => s.id === slotId ? { ...s, preview: url, file } : s)
    );
  };

  const handleRemove = (slotId: string) => {
    setUploadSlots((prev) =>
      prev.map((s) => s.id === slotId ? { ...s, preview: null, file: null } : s)
    );
  };

  const canSend = (input.trim().length > 0 || uploadSlots.some((s) => s.preview)) && !isSending;

  // ── 메시지 전송 ───────────────────────────────────────────────────────
  const handleSend = async () => {
    if (!canSend) return;

    const trimmedInput      = input.trim();
    const previews          = uploadSlots.filter((s) => s.preview).map((s) => s.preview!);
    const slotFiles         = uploadSlots.filter((s) => s.file).map((s) => s.file!);
    const currentAnalysisType = analysisType;

    // 업로드 이미지를 미리보기(blob URL)로 즉시 메시지에 표시
    const userMsg: Message = {
      id     : Date.now(),
      role   : "user",
      content: trimmedInput || `${ANALYSIS_OPTIONS.find(o => o.value === currentAnalysisType)?.label || "분석"} 요청`,
      images : previews.length > 0 ? previews : undefined,
      time   : new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setUploadSlots(getUploadSlots(currentAnalysisType));
    setAnalysisType("default");
    setIsSending(true);
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    // 비로그인 첫 메시지 전송 시 게스트 채팅 카운트 증가
    const isFirstGuestMessage = !isLoggedIn && messages.length === 0;
    if (isFirstGuestMessage) {
      const prev = parseInt(localStorage.getItem("guest_chat_count") ?? "0", 10);
      localStorage.setItem("guest_chat_count", String(prev + 1));
    }

    try {
      if (!isLoggedIn) {
        // 비로그인: 게스트 엔드포인트 사용 (DB 저장 없음)
        const result = await sendGuestMessage(trimmedInput);
        const aiMsg: Message = {
          id     : Date.now() + 1,
          role   : "bot",
          content: result.content,
          time   : new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, aiMsg]);
      } else {
        // 1. 이미지 파일들을 S3에 업로드하여 실제 URL 획득
        let s3Urls: string[] = [];
        if (slotFiles.length > 0) {
          s3Urls = await Promise.all(slotFiles.map((file) => uploadImage(file, currentAnalysisType)));
        }

        // 2. 채팅방이 없으면 먼저 생성
        let roomId = chatRoomId;
        const isNewRoom = roomId === null;
        if (roomId === null) {
          const room = await createChatRoom();
          roomId = room.chat_room_id;
          skipFetchRef.current = true; // fetchMessages useEffect 건너뜀
          setChatRoomId(roomId);
        }

        // 3. 메시지 전송 (S3 URL 포함)
        const result = await sendMessage(roomId, {
          content   : userMsg.content,
          model_type: currentAnalysisType !== "default" ? currentAnalysisType : undefined,
          image_url : s3Urls.length > 0 ? s3Urls : undefined,
        });

        if (isNewRoom) {
          // 새 채팅방: 낙관적 유저 메시지를 API 결과로 교체 (user + bot 모두 포함)
          setMessages((prev) => {
            const withoutOptimistic = prev.filter((m) => m.id !== userMsg.id);
            return [...withoutOptimistic, ...result.map(apiMsgToMessage)];
          });
        } else {
          // 기존 채팅방: 봇 메시지만 추가
          const aiMsg = result.find((m) => m.role === "assistant");
          if (aiMsg) setMessages((prev) => [...prev, apiMsgToMessage(aiMsg)]);
        }
      }
    } catch (err) {
      console.error("메시지 전송 실패:", err);
    } finally {
      setIsSending(false);
    }
  };

  // ── 드래그 앤 드롭 이미지 업로드 (미구현) ─────────────────────────
  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) handleImageUpload(file);
  };

  const handleImageUpload = (file: File) => {
    const url = URL.createObjectURL(file);
    const userMsg: Message = {
      id     : Date.now(),
      role   : "user",
      content: "피부 이미지를 분석해 주세요",
      image  : url,
      time   : new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);
    setTimeout(() => {
      const botMsg: Message = {
        id     : Date.now() + 1,
        role   : "bot",
        content: "이미지를 분석하고 있어요... ✨\n\n분석이 완료되면 피부 상태와 맞춤 제품을 추천해 드릴게요!",
        time   : new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
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
        {isLoadingHistory ? (
          <div className="flex flex-col items-center justify-center h-full">
            <video src={loadingWebm} autoPlay loop muted playsInline className="w-30 h-auto" />
            <p className="text-sm text-gray-500">채팅 내역 불러오는 중...</p>
          </div>
        ) : !chat_content && messages.length === 0 ? (
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
                    <div
                      className={`rounded-2xl text-sm leading-relaxed overflow-hidden ${
                        msg.role === "user"
                          ? "text-white rounded-br-md shadow-sm bg-[#84c13d]"
                          : "text-gray-800 bg-white border border-gray-100 shadow-sm rounded-bl-md"
                      }`}
                    >
                      {/* 단일 이미지 */}
                      {msg.image && (
                        <div
                          className="relative overflow-hidden cursor-pointer group p-3 pb-0"
                          onClick={() => setExpandedImage(msg.image!)}
                        >
                          <img src={msg.image} alt="Uploaded" className="w-[130px] h-[130px] object-cover rounded-2xl" />
                          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                            <ZoomIn className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                          </div>
                        </div>
                      )}
                      {/* 복수 이미지 */}
                      {msg.images && msg.images.length > 0 && (
                        <div className={`grid gap-0.5 ${
                          msg.images.length === 1 ? "grid-cols-1" :
                          msg.images.length === 2 ? "grid-cols-2" :
                          "grid-cols-3"
                        }`}>
                          {msg.images.map((img, idx) => (
                            <div
                              key={idx}
                              className="relative overflow-hidden cursor-pointer group p-3 pb-0"
                              onClick={() => setExpandedImage(img)}
                            >
                              <img src={img} alt="Uploaded" className="w-[130px] h-[130px] object-cover rounded-2xl" />
                              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                                <ZoomIn className="w-5 h-5 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      {/* 텍스트 */}
                      <div className="px-4 py-3">
                        {msg.role === "bot" ? (
                          <ReactMarkdown
                            components={{
                              p:      ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                              em:     ({ children }) => <em className="italic">{children}</em>,
                              ul:     ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                              ol:     ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                              li:     ({ children }) => <li className="text-sm leading-relaxed">{children}</li>,
                              h1:     ({ children }) => <h1 className="text-base font-bold mb-2">{children}</h1>,
                              h2:     ({ children }) => <h2 className="text-sm font-bold mb-1">{children}</h2>,
                              h3:     ({ children }) => <h3 className="text-sm font-semibold mb-1">{children}</h3>,
                              code:   ({ children }) => <code className="bg-gray-100 rounded px-1 text-xs font-mono">{children}</code>,
                              hr:     () => <hr className="my-2 border-gray-200" />,
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        ) : (
                          <span className="whitespace-pre-wrap">{msg.content}</span>
                        )}
                      </div>
                    </div>
                    <span className="text-[10px] text-gray-400 px-1">{msg.time}</span>
                  </div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1 overflow-hidden">
                      <img
                        src={defaultProfile}
                        alt="User"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {isSending && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="p-2 py-4">
                <video src={loadingWebm} autoPlay loop muted playsInline className="w-19 h-auto" />
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
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold px-3 py-1 rounded-lg text-white" style={{ background: "#84C13D" }}>
                    {ANALYSIS_OPTIONS.find((o) => o.value === analysisType)?.label}
                  </span>
                  <span className="text-[11px] text-gray-400">{ANALYSIS_HINTS[analysisType]}</span>
                </div>
                <button className="p-1 cursor-pointer" onClick={() => { setUploadSlots(getUploadSlots('default')); setAnalysisType("default"); }}>
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>
              <div className="flex items-center">
                <div className="flex flex-row max-w-[1000px]">
                  <div className="flex items-center justify-center">
                    <img src={ analysisType === 'ingredient' ? infoImg2 : infoImg1 } alt="" />
                  </div>
                  <div className="w-px self-stretch bg-gray-100 mx-4" />
                  <div className={`basis-1/2 grid place-content-center gap-3 ${uploadSlots.length === 1 ? "grid-cols-1 max-w-[150px]" : uploadSlots.length === 3 ? "grid-cols-3 max-w-[450px]" : "grid-cols-2"}`}>
                    {uploadSlots.map((slot) => (
                      <UploadSlotCard key={slot.id} slot={slot} onUpload={handleUpload} onRemove={handleRemove} />
                    ))}
                  </div>
                </div>
              </div>

          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-100 px-4 py-3 flex-shrink-0">
        <div className="flex items-end gap-2 bg-gray-50 rounded-2xl px-3 py-2 border-1 border-transparent focus-within:border-[#84C13D] transition-colors">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="지금, AI와 피부 고민을 나눠보세요."
            className="flex-1 bg-transparent resize-none text-sm text-gray-800 placeholder-gray-400 outline-none max-h-[120px] leading-relaxed py-1.5"
            rows={1}
          />

          {/* 분석 유형 선택 */}
          <div className="relative flex-shrink-0">
            {isLoggedIn ? (
              /* 로그인 상태 — 정상 동작 */
              <>
                <button
                  onClick={() => setAnalysisDropdownOpen(!analysisDropdownOpen)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
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
                          className={`w-full text-left px-4 py-2.5 text-xs font-medium transition-colors cursor-pointer ${
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
              </>
            ) : (
              /* 비로그인 상태 — 잠금 버튼 (클릭 시 토스트) */
              <button
                onClick={triggerAnalysisToast}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border border-gray-200 text-gray-400 bg-white cursor-pointer"
              >
                <Lock className="w-3 h-3" />
                <span className="whitespace-nowrap">분석 선택</span>
              </button>
            )}
          </div>
          {/* 전송 버튼 */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <motion.button
              onClick={handleSend}
              disabled={!canSend}
              whileTap={{ scale: 0.9 }}
              className="w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 cursor-pointer"
            >
              <Icon name={canSend ? "send_active" : "send_disable"} size={36} />
            </motion.button>
          </div>
        </div>
        <p className="text-[11px] text-gray-400 text-center mt-2">
          Enter 전송 · Shift+Enter 줄바꿈
        </p>
      </div>

      {/* 분석 기능 로그인 안내 토스트 */}
      <AnimatePresence>
        {showAnalysisToast && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-3 rounded-2xl shadow-lg text-sm"
            style={{ background: "#1F2937", color: "white", minWidth: "260px", maxWidth: "340px" }}
          >
            <Lock className="w-4 h-4 flex-shrink-0" style={{ color: "#84C13D" }} />
            <span className="flex-1 text-xs leading-relaxed">
              분석 기능은 <strong>회원 전용</strong> 기능입니다.
            </span>
            <Link
              to="/login"
              className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={{ background: "#84C13D", color: "white" }}
              onClick={() => setShowAnalysisToast(false)}
            >
              로그인
            </Link>
          </motion.div>
        )}
      </AnimatePresence>

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
