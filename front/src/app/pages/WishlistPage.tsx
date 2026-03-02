import { ExternalLink } from "lucide-react";
import { motion } from "motion/react";
import { useState, useEffect } from "react";
import loadingWebm from "@/assets/animations/logo_loop_1.webm";
import { Heart, Loader2, PackageOpen, Trash2 } from "lucide-react";
import { fetchWishlist, removeFromWishlist, type WishlistItem } from "@/app/api/wishlistApi";

/** added_at ISO 문자열 → "YYYY.MM.DD" 형식 변환 */
function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

export function WishlistPage() {
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [removingIds, setRemovingIds] = useState<Set<number>>(new Set());

  // ─── 위시리스트 조회 (back: GET /wishlist) ───
  useEffect(() => {
    setIsLoading(true);
    fetchWishlist()
      .then(setItems)
      .catch((err: Error) => setFetchError(err.message))
      .finally(() => setIsLoading(false));
  }, []);

  // ─── 위시리스트 삭제 (back: DELETE /wishlist/{wish_id}) ───
  const handleRemove = async (wishId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setRemovingIds((prev) => new Set(prev).add(wishId));
    try {
      await removeFromWishlist(wishId);
      setItems((prev) => prev.filter((item) => item.wish_id !== wishId));
    } catch (err) {
      console.error("위시리스트 삭제 실패:", err);
    } finally {
      setRemovingIds((prev) => {
        const next = new Set(prev);
        next.delete(wishId);
        return next;
      });
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-[#F8FBF3]">
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-gray-900 font-bold">위시리스트</h1>
            <p className="text-sm text-gray-500 mt-0.5">AI가 추천한 내 피부 맞춤 제품</p>
          </div>
          {!isLoading && !fetchError && (
            <span className="px-3 py-1.5 rounded-xl text-sm font-semibold text-white" style={{ background: "#84C13D" }}> {items.length}개 저장됨 </span>
          )}
        </div>

        {/* 로딩 */}
        {isLoading && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center justify-center py-20">
            <video src={loadingWebm} autoPlay loop muted playsInline className="w-30 h-auto" />
            <p className="text-sm text-gray-500">불러오는 중...</p>
          </motion.div>
        )}

        {/* 에러 */}
        {!isLoading && fetchError && (
          <div className="py-10 text-center text-sm text-red-500">{fetchError}</div>
        )}

        {/* 빈 목록 */}
        {!isLoading && !fetchError && items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <PackageOpen className="w-14 h-14 mb-3 opacity-40" />
            <p className="text-sm font-medium">저장된 제품이 없습니다</p>
            <p className="text-xs mt-1">AI 채팅에서 추천받은 제품을 저장해보세요</p>
          </div>
        )}

        {/* 목록 */}
        {!isLoading && !fetchError && items.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            {items.map((item, idx) => (
              <motion.div
                key={item.wish_id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25, delay: idx * 0.05 }}
                className={idx < items.length - 1 ? "border-b border-gray-50" : ""}
              >
                <div className="flex items-center gap-3 px-4 py-3.5">
                  {/* 하트 아이콘 */}
                  <div className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
                    style={{ background: "#E8F5D0" }}>
                    <Heart className="w-4 h-4" style={{ color: "#84C13D", fill: "#84C13D" }} />
                  </div>

                  {/* 제목 + 추가일 */}
                  <a
                    href={item.product_description ?? undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`flex-1 min-w-0 group ${item.product_description ? "cursor-pointer" : "cursor-default"}`}
                  >
                    <p className="text-sm font-medium text-gray-800 truncate group-hover:text-[#84C13D] transition-colors">
                      {item.product_name}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">{formatDate(item.added_at)}</p>
                  </a>

                  {/* 외부 링크 이동 아이콘 */}
                  {item.product_description && (
                    <a
                      href={item.product_description}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-shrink-0 text-gray-300 hover:text-[#84C13D] transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}

                  {/* 삭제 버튼 */}
                  <button
                    onClick={(e) => handleRemove(item.wish_id, e)}
                    disabled={removingIds.has(item.wish_id)}
                    className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center text-gray-300 cursor-pointer hover:text-red-400 hover:bg-red-50 transition-all disabled:opacity-40"
                  >
                    {removingIds.has(item.wish_id)
                      ? <Loader2 className="w-4 h-4 animate-spin" />
                      : <Trash2 className="w-4 h-4" />
                    }
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}