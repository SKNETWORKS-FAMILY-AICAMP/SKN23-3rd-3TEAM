import { useState } from "react";
import { Outlet } from "react-router";
import { Menu } from "lucide-react";
import { Sidebar } from "./Sidebar";

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-[#F8FBF3] overflow-hidden">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-gray-100 flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
            aria-label="메뉴 열기"
          >
            <Menu className="w-5 h-5 text-gray-600" />
          </button>
          {/* <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #84C13D, #6BA32E)" }}
            >
              <span className="text-white text-xs font-bold">S</span>
            </div>
            <span className="text-gray-900 font-semibold text-sm">SKIN AI</span>
          </div> */}
          <div className="w-9" />
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
