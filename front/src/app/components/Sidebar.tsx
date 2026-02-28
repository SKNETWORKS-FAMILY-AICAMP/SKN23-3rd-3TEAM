import { useState, useEffect } from "react";
import { Icon } from "@/app/components/ui/icon"
import { X, Plus, LogOut, Settings } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router";
import { fetchChatRooms, type ChatRoom } from "@/app/api/chatApi";
import { fetchCurrentUser, logout, type UserResponse } from "@/app/api/userApi";

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
  const [user, setUser] = useState<UserResponse | null>(null);

  const navItems = [
    { path: "/analysis", label: "피부 분석", icon: 'beauty' as const },
    { path: "/wishlist", label: "위시리스트", icon: 'wish' as const },
  ];

  // 채팅방 목록 + 사용자 정보 조회
  useEffect(() => {
    fetchChatRooms()
      .then(setChatRooms)
      .catch((err: Error) => console.error("채팅방 목록 조회 실패:", err));

    fetchCurrentUser()
      .then(setUser)
      .catch((err: Error) => console.error("사용자 정보 조회 실패:", err));
  }, []);

  const handleNewChat = () => {
    setActiveChatId(null);
    navigate("/chat");
    onClose();
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
        style={{
          boxShadow: "2px 0 12px rgba(133,193,61,0.08)",
        }}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-gray-50">
          <Link to="/chat" className="flex items-center gap-2.5 group" onClick={onClose}>
            <img src="/src/assets/logo.svg" alt="LOGO" style={{width: '50px'}} />
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
            const isActive =
              location.pathname === item.path ||
              location.pathname.startsWith(item.path + "/");
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={`flex items-center gap-3 px-3 py-2.5 mb-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "text-white"
                    : "text-gray-600 hover:text-gray-900"
                }`}
                style={
                  isActive
                    ? {
                        background:
                          "linear-gradient(135deg, #84C13D, #6BA32E)",
                        boxShadow:
                          "0 2px 8px rgba(133,193,61,0.25)",
                      }
                    : {}
                }
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background =
                      "#F0FAE3";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = "";
                  }
                }}
              >
                <Icon name={item.icon} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Chat History */}
        <div className="px-4 pt-3 pb-2 flex-1 overflow-y-auto">
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-2 mb-2">
            최근 채팅
          </p>
          <div className="space-y-1">
            {chatRooms.map((chat) => {
              const isActive = location.pathname === "/chat" && activeChatId === chat.chat_room_id;

              return (
                <button
                  key={chat.chat_room_id}
                  onClick={() => {
                    setActiveChatId(chat.chat_room_id);
                    navigate("/chat", { state: { chat_room_id: chat.chat_room_id } });
                    onClose();
                  }}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer ${
                    isActive
                      ? "bg-[#E8F5D0]"
                      : "hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon name="chat" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-0.5">
                        <p
                          className="text-xs font-semibold truncate"
                          style={{
                            color: isActive
                              ? "#4A7A1E"
                              : "#374151",
                          }}
                        >
                          {chat.title ?? "새 채팅"}
                        </p>
                        <span className="text-[10px] text-gray-400 flex-shrink-0 ml-1">
                          {formatRelativeDate(chat.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Profile / Bottom nav */}
        <div className="border-t border-gray-100 ">
          <Link
            to="/settings"
            onClick={onClose}
            className="flex items-center gap-2.5 flex-1 px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="relative flex-shrink-0">
              <img
                src={user?.profile_image_url ?? "https://images.unsplash.com/photo-1634469875582-a0885fc2f589?w=40&h=40&fit=crop"}
                alt="Profile"
                className="w-8 h-8 rounded-full object-cover border-2"
                style={{ borderColor: "#84C13D" }}
              />
              <span
                className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white"
                style={{ background: "#84C13D" }}
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-gray-800 truncate">
                {user?.nickname ?? user?.name ?? ""}
              </p>
              <p className="text-[11px] text-gray-400 truncate">
                { user?.email ?? "" }
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
              style={
                location.pathname === "/settings"
                  ? { background: "#84C13D" }
                  : {}
              }
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
      </aside>
    </>
  );
}
