import { useState } from "react";
import { Icon } from "@/app/components/ui/icon"
import { X, Plus, LogOut, Settings } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router";

const MOCK_CHATS = [
  {
    id: 1,
    title: "피부 분석 요청",
    preview: "수분 부족형 복합성 피부로...",
    time: "오늘",
  },
  {
    id: 2,
    title: "보습 크림 추천",
    preview: "세라마이드 함유 제품을...",
    time: "어제",
  },
  {
    id: 3,
    title: "여드름 케어 방법",
    preview: "살리실산 성분 클렌저를...",
    time: "어제",
  },
  {
    id: 4,
    title: "선크림 추천해줘",
    preview: "SPF50+ PA++++ 제품으로...",
    time: "2일 전",
  },
  {
    id: 5,
    title: "피부 타입 체크",
    preview: "T존 지성, 볼 건성 복합성...",
    time: "3일 전",
  },
];

interface SidebarProps { isOpen: boolean; onClose: () => void; }

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeChatId, setActiveChatId] = useState<number | null>(1);

  const navItems = [
    { path: "/analysis", label: "피부 분석", icon: 'beauty' as const },
    { path: "/wishlist", label: "위시리스트", icon: 'wish' as const },
  ];

  const handleNewChat = () => {
    setActiveChatId(null);
    navigate("/chat", { state: { chat_content: false } });
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
            className="w-full flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group cursor-pointer"
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
        <nav className="px-4 pt-2 pb-1">
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
                className={`flex items-center gap-3 px-2 py-1.5 rounded-xl text-sm font-medium transition-all duration-200 ${
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
            {MOCK_CHATS.map((chat) => {
              const isActive = location.pathname === "/chat" && activeChatId === chat.id;

              return (
                <button
                  key={chat.id}
                  onClick={() => {
                    setActiveChatId(chat.id);
                    navigate("/chat", { state: { chat_content: true } });
                    onClose();
                  }}
                  className={`w-full text-left px-3 py-2.5 rounded-xl transition-all duration-200 group ${
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
                          {chat.title}
                        </p>
                        <span className="text-[10px] text-gray-400 flex-shrink-0 ml-1">
                          {chat.time}
                        </span>
                      </div>
                      <p className="text-[11px] text-gray-400 truncate">
                        {chat.preview}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Profile / Bottom nav */}
        <div className="border-t border-gray-100 px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <Link
              to="/settings"
              onClick={onClose}
              className="flex items-center gap-2.5 flex-1 px-3 py-2.5 rounded-xl hover:bg-gray-50 transition-colors"
            >
              <div className="relative">
                <img
                  src="https://images.unsplash.com/photo-1634469875582-a0885fc2f589?w=40&h=40&fit=crop"
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
                  김민지
                </p>
                <p className="text-[11px] text-gray-400 truncate">
                  복합성 피부
                </p>
              </div>
            </Link>
          </div>
          <div className="flex gap-1">
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
            <Link
              to="/login"
              onClick={onClose}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              로그아웃
            </Link>
          </div>
        </div>
      </aside>
    </>
  );
}