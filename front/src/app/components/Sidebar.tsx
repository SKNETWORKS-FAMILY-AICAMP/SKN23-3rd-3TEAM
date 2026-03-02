import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Icon } from "@/app/components/ui/icon"
import defaultProfile from "@/assets/profile.png"
import { Plus, LogIn, LogOut, Settings, Lock, Trash2 } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router";
import { fetchChatRooms, deleteChatRoom, type ChatRoom } from "@/app/api/chatApi";
import { fetchCurrentUser, type UserResponse } from "@/app/api/userApi";
import { logout } from "@/app/api/authApi";
import LOGO from "@/assets/logo.png";

interface GuestChatRoom {
  id         : string;
  title      : string;
  created_at : string;
  messages   : { role: "user" | "bot"; content: string; time: string }[];
}

/** 생성일 → 상대적 날짜 표시 ("오늘", "어제", "N일 전") */
function formatRelativeDate(iso: string): string {
  const now = new Date();
  const d = new Date(iso);
  const diffDays = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "오늘";
  if (diffDays === 1) return "어제";
  return `${diffDays}일 전`;
}

interface SidebarProps { isOpen: boolean; onClose: () => void; }

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [guestChats, setGuestChats] = useState<GuestChatRoom[]>([]);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [showMenuToast, setShowMenuToast]           = useState(false);
  const [showChatLimitToast, setShowChatLimitToast] = useState(false);
  const toastTimerRef      = useRef<ReturnType<typeof setTimeout> | null>(null);
  const chatLimitTimerRef  = useRef<ReturnType<typeof setTimeout> | null>(null);

  const triggerMenuToast = () => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setShowMenuToast(true);
    toastTimerRef.current = setTimeout(() => setShowMenuToast(false), 3000);
  };

  const triggerChatLimitToast = () => {
    if (chatLimitTimerRef.current) clearTimeout(chatLimitTimerRef.current);
    setShowChatLimitToast(true);
    chatLimitTimerRef.current = setTimeout(() => setShowChatLimitToast(false), 3000);
  };

  const navItems = [
    { path: "/analysis", label: "피부 분석", icon: 'beauty' as const },
    { path: "/wishlist", label: "위시리스트", icon: 'wish' as const },
  ];

  const isLoggedIn = !!localStorage.getItem("access_token");

  // 채팅방 목록 + 사용자 정보 조회 (로그인 상태일 때만)
  useEffect(() => {
    if (!isLoggedIn) return;

    fetchChatRooms()
      .then(setChatRooms)
      .catch((err: Error) => console.error("채팅방 목록 조회 실패:", err));

    fetchCurrentUser()
      .then(setUser)
      .catch((err: Error) => console.error("사용자 정보 조회 실패:", err));
  }, [isLoggedIn]);

  // 게스트 채팅 목록 로드 + 업데이트 이벤트 구독 (비로그인 상태일 때만)
  useEffect(() => {
    if (isLoggedIn) return;

    const load = () => {
      const stored = JSON.parse(localStorage.getItem("guest_chats") ?? "[]") as GuestChatRoom[];
      setGuestChats(stored);
    };
    load();
    window.addEventListener("guestChatUpdated", load);
    return () => window.removeEventListener("guestChatUpdated", load);
  }, [isLoggedIn]);

  const GUEST_CHAT_LIMIT = 5;

  const handleNewChat = () => {
    if (!isLoggedIn) {
      const count = parseInt(localStorage.getItem("guest_chat_count") ?? "0", 10);
      if (count >= GUEST_CHAT_LIMIT) {
        triggerChatLimitToast();
        return;
      }
    }
    setActiveChatId(null);
    navigate("/chat");
    onClose();
  };

  // 게스트 채팅방 삭제
  const handleDeleteGuestChat = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const stored = JSON.parse(localStorage.getItem("guest_chats") ?? "[]") as GuestChatRoom[];
    const updated = stored.filter((r) => r.id !== id);
    localStorage.setItem("guest_chats", JSON.stringify(updated));
    localStorage.setItem("guest_chat_count", String(updated.length));
    setGuestChats(updated);
    if (location.state?.guest_chat_id === id) {
      navigate("/chat");
    }
  };

  // 채팅방 삭제
  const handleDeleteChat = async (e: React.MouseEvent, chatRoomId: number) => {
    e.stopPropagation();
    try {
      await deleteChatRoom(chatRoomId);
      setChatRooms(prev => prev.filter(r => r.chat_room_id !== chatRoomId));
      if (activeChatId === chatRoomId) {
        setActiveChatId(null);
        navigate("/chat");
      }
    } catch (err) {
      console.error("채팅방 삭제 실패:", err);
    }
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-[260px] z-50 flex flex-col
          bg-white border-r border-gray-100
          transition-transform duration-300 ease-in-out
          lg:static lg:translate-x-0 lg:z-auto
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
        style={{ boxShadow: "2px 0 12px rgba(133,193,61,0.08)" }}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-gray-50">
          <Link to="/chat" className="flex items-center gap-2.5 group" onClick={onClose}>
            <img src={LOGO} alt="LOGO" />
          </Link>
        </div>

        {/* New Chat Button */}
        <div className="px-4 pt-4 pb-2">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 group cursor-pointer"
            style={{
              background: "#84C13D",
              color: "white",
              boxShadow: "0 2px 8px rgba(133,193,61,0.3)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow =
                "0 4px 14px rgba(133,193,61,0.45)";
              e.currentTarget.style.transform =
                "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow =
                "0 2px 8px rgba(133,193,61,0.3)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <Plus className="w-4.5 h-4.5" />
            새로운 채팅 추가
          </button>
        </div>

        {/* Navigation */}
        <nav className="px-4 pt-3">
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-2 mb-2">
            메뉴
          </p>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + "/");
            const commonClass = `w-full flex items-center gap-3 px-3 py-2.5 mb-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
              isActive ? "text-white" : "text-gray-600"
            }`;
            const activeStyle = isActive ? { background: "#84C13D", boxShadow: "0 2px 8px rgba(133,193,61,0.25)" } : {};

            if (!isLoggedIn) {
              return (
                <button
                  key={item.path}
                  onClick={triggerMenuToast}
                  className={`${commonClass} cursor-pointer`}
                  style={activeStyle}
                  onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "#F0FAE3"; }}
                  onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = ""; }}
                >
                  <Icon name={item.icon} />
                  {item.label}
                </button>
              );
            }
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={commonClass}
                style={activeStyle}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "#F0FAE3"; }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = ""; }}
              >
                <Icon name={item.icon} variant={isActive ? 'white' : 'green'} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Chat History — 로그인 상태에서만 표시 */}
        <div className="px-4 pt-3 pb-2 flex-1 overflow-y-auto">
          {isLoggedIn ? (
            <>
              <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-2 mb-2">
                최근 채팅
              </p>
              <div className="space-y-1">
                {chatRooms.map((chat) => {
                  const isActive = location.pathname === "/chat" && activeChatId === chat.chat_room_id;
                  return (
                    <div
                      key={chat.chat_room_id}
                      onClick={() => {
                        setActiveChatId(chat.chat_room_id);
                        navigate("/chat", { state: { chat_room_id: chat.chat_room_id } });
                        onClose();
                      }}
                      className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer ${
                        isActive ? "bg-[#E8F5D0]" : "hover:bg-gray-50"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon name="chat" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-0.5">
                            <p className="text-xs font-semibold truncate" style={{ color: isActive ? "#4A7A1E" : "#374151" }}>
                              {chat.title ?? "새 채팅"}
                            </p>
                            <div className="flex-shrink-0 ml-1" style={{height: '16px'}}>
                              <span className="text-[10px] text-gray-400 group-hover:hidden">
                                {formatRelativeDate(chat.created_at)}
                              </span>
                              <button
                                onClick={(e) => handleDeleteChat(e, chat.chat_room_id)}
                                className="hidden group-hover:flex items-center justify-center p-0.5 rounded text-gray-400 hover:text-red-500 transition-colors cursor-pointer"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <>
              <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-2 mb-2">
                최근 채팅
              </p>
              <div className="space-y-1">
                {guestChats.map((chat) => {
                  const isActive = location.pathname === "/chat" && location.state?.guest_chat_id === chat.id;
                  return (
                    <div
                      key={chat.id}
                      onClick={() => {
                        navigate("/chat", { state: { guest_chat_id: chat.id } });
                        onClose();
                      }}
                      className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer ${
                        isActive ? "bg-[#E8F5D0]" : "hover:bg-gray-50"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon name="chat" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-0.5">
                            <p className="text-xs font-semibold truncate" style={{ color: isActive ? "#4A7A1E" : "#374151" }}>
                              {chat.title}
                            </p>
                            <div className="flex-shrink-0 ml-1" style={{ height: "16px" }}>
                              <span className="text-[10px] text-gray-400 group-hover:hidden">
                                {formatRelativeDate(chat.created_at)}
                              </span>
                              <button
                                onClick={(e) => handleDeleteGuestChat(e, chat.id)}
                                className="hidden group-hover:flex items-center justify-center p-0.5 rounded text-gray-400 hover:text-red-500 transition-colors cursor-pointer"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {guestChats.length === 0 && (
                  <p className="text-xs text-gray-400 text-center py-4">
                    아직 채팅 기록이 없어요
                  </p>
                )}
              </div>
            </>
          )}
        </div>

        {/* Profile / Bottom nav */}
        {!isLoggedIn && (
          <div className="border-t border-gray-100 px-4 py-3">
            <Link
              to="/login"
              onClick={onClose}
              className="w-full flex gap-1.5 items-center justify-center py-2.5 rounded-lg text-xs font-semibold text-white transition-all"
              style={{ background: "#84C13D", boxShadow: "0 2px 8px rgba(133,193,61,0.3)" }}
            >
              <LogIn className="w-3.5 h-3.5" />
              로그인
            </Link>
          </div>
        )}
        {isLoggedIn && (
          <div className="border-t border-gray-100">
            <Link
              to="/settings"
              onClick={onClose}
              className="flex items-center gap-2.5 flex-1 px-4 py-3 hover:bg-gray-50 transition-colors"
            >
              <div className="relative flex-shrink-0">
                <img
                  src={user?.profile_image_url ?? defaultProfile}
                  alt="Profile"
                  className="w-8 h-8 rounded-full object-cover border-2"
                  style={{ borderColor: "#84C13D" }}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-gray-800 truncate">
                  {user?.nickname ?? user?.name ?? ""}
                </p>
                <p className="text-[11px] text-gray-400 truncate">
                  {user?.email ?? ""}
                </p>
              </div>
            </Link>
            <div className="flex gap-1 px-4 py-2 pb-3">
              <Link
                to="/settings"
                onClick={onClose}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                  location.pathname === "/settings"
                    ? "text-white"
                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                }`}
                style={location.pathname === "/settings" ? { background: "#84C13D" } : {}}
              >
                <Settings className="w-3.5 h-3.5" />
                설정
              </Link>
              <button
                onClick={() => { logout(); navigate("/login", { replace: true }); onClose(); }}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium text-gray-500 hover:text-red-500 hover:bg-red-50 transition-colors cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                로그아웃
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* 회원 전용 메뉴 토스트 */}
      <AnimatePresence>
        {showMenuToast && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-3 px-4 py-3 rounded-2xl shadow-lg text-sm"
            style={{ background: "#1F2937", color: "white", minWidth: "260px", maxWidth: "340px" }}
          >
            <Lock className="w-4 h-4 flex-shrink-0" style={{ color: "#84C13D" }} />
            <span className="flex-1 text-xs leading-relaxed">
              이 메뉴는 <strong>회원 전용</strong> 기능입니다.
            </span>
            <Link
              to="/login"
              className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={{ background: "#84C13D", color: "white" }}
              onClick={() => setShowMenuToast(false)}
            >
              로그인
            </Link>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 비로그인 채팅 한도 초과 토스트 */}
      <AnimatePresence>
        {showChatLimitToast && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-3 px-4 py-3 rounded-2xl shadow-lg text-sm"
            style={{ background: "#1F2937", color: "white", minWidth: "260px", maxWidth: "340px" }}
          >
            <Lock className="w-4 h-4 flex-shrink-0" style={{ color: "#84C13D" }} />
            <span className="flex-1 text-xs leading-relaxed">
              채팅방은 최대 <strong>{GUEST_CHAT_LIMIT}개</strong>까지 생성할 수 있어요.<br />
              추가 생성은 <strong>로그인</strong>이 필요합니다.
            </span>
            <Link
              to="/login"
              className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={{ background: "#84C13D", color: "white" }}
              onClick={() => setShowChatLimitToast(false)}
            >
              로그인
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
