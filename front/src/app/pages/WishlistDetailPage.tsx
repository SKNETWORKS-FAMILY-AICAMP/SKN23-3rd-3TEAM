import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import {
  ChevronLeft,
  Heart,
  Share2,
  ChevronDown,
  Loader2,
  Trash2,
  CalendarDays,
  Tag,
} from "lucide-react";
import { motion } from "motion/react";
import loadingWebm from "@/assets/animations/logo_loop_1.webm";
import { fetchWishlistItem, removeFromWishlist, type WishlistItem } from "@/app/api/wishlistApi";

/** added_at ISO 문자열 → "YYYY.MM.DD" 형식 변환 */
function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

export function WishlistDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [item, setItem] = useState<WishlistItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [isRemoving, setIsRemoving] = useState(false);
  const [expandedDesc, setExpandedDesc] = useState(true);

  // ─── 단건 조회 (back: GET /wishlist/{wish_id}) ───
  useEffect(() => {
    if (!id) return;
    setIsLoading(true);
    fetchWishlistItem(Number(id))
      .then(setItem)
      .catch((err: Error) => setFetchError(err.message))
      .finally(() => setIsLoading(false));
  }, [id]);

  // ─── 위시리스트 삭제 (back: DELETE /wishlist/{wish_id}) ───
  const handleRemove = async () => {
    if (!item) return;
    setIsRemoving(true);
    try {
      await removeFromWishlist(item.wish_id);
      navigate("/wishlist");
    } catch (err) {
      console.error("삭제 실패:", err);
      setIsRemoving(false);
    }
  };

  // ── 로딩 ──
  if (isLoading) {
    return (
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center justify-center py-20">
        <video src={loadingWebm} autoPlay loop muted playsInline className="w-30 h-auto" />
        <p className="text-sm text-gray-500">불러오는 중...</p>
      </motion.div>
    );
  }

  // ── 에러 / 없음 ──
  if (fetchError || !item) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-500 font-medium">{fetchError ?? "제품을 찾을 수 없습니다"}</p>
          <button
            onClick={() => navigate("/wishlist")}
            className="mt-3 text-sm hover:underline"
            style={{ color: "#84C13D" }}
          >
            위시리스트로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-[#F8FBF3]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-sm border-b border-gray-100 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate("/wishlist")}
          className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <h2 className="flex-1 text-sm font-semibold text-gray-800 truncate">{item.product_name}</h2>
        <button className="p-2 rounded-xl hover:bg-gray-100 transition-colors">
          <Share2 className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-5 space-y-4">
        {/* 제품 정보 */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="flex bg-white rounded-2xl p-5 border border-gray-100 shadow-sm space-y-4"
        >
          <div className="flex-shrink-0">
            <h1 className="text-gray-900 font-bold leading-snug">{item.product_name}</h1>

            {/* 메타 정보 */}
            <div className="flex flex-wrap gap-3 text-xs text-gray-400 mt-2">
              <span className="flex items-center gap-1">
                <CalendarDays className="w-3.5 h-3.5" />
                저장일 {formatDate(item.added_at)}
              </span>
              {/* <span className="flex items-center gap-1">
                <Tag className="w-3.5 h-3.5" />
                {item.product_vector_id}
              </span> */}
            </div>
          </div>
          {/* 삭제 버튼 */}
          <button
            onClick={handleRemove}
            disabled={isRemoving}
            className="ml-auto flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center text-gray-300 cursor-pointer hover:text-red-400 hover:bg-red-50 transition-all disabled:opacity-40"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </motion.div>

        {/* 제품 설명 아코디언 */}
        {item.product_description && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.15 }}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden"
          >
            <button
              onClick={() => setExpandedDesc(!expandedDesc)}
              className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold text-gray-800 hover:bg-gray-50 transition-colors"
            >
              제품 설명
              <ChevronDown
                className="w-5 h-5 text-gray-300 mr-1 transition-transform duration-200"
                style={{ transform: expandedDesc ? "rotate(180deg)" : "" }}
              />
            </button>
            {expandedDesc && (
              <div className="px-5 pb-4 border-t border-gray-50">
                <p className="text-sm text-gray-600 leading-relaxed pt-3">
                  {item.product_description}
                </p>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}
