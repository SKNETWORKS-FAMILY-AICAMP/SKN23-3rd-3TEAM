import { motion } from "motion/react";
import { ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";
import { useState, useEffect } from "react";
import { Loading } from "@/app/components/ui/loading";
import { Heart, Loader2, PackageOpen } from "lucide-react";
import { fetchWishlist, addToWishlist, removeFromWishlist, type WishlistItem } from "@/app/api/wishlistApi";

const PAGE_SIZE = 10;

/** added_at ISO 문자열 → "YYYY.MM.DD" 형식 변환 */
function formatDate(iso: string): string {
    const d = new Date(iso);

    return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

/** 페이지네이션 버튼 목록 생성 (최대 5개, 말줄임 포함) */
function getPageNumbers(current: number, total: number): (number | "...")[] {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

    const pages: (number | "...")[] = [1];

    if (current > 3) pages.push("...");

    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
        pages.push(i);
    }

    if (current < total - 2) pages.push("...");

    pages.push(total);

    return pages;
}

export function WishlistPage() {
    const [items, setItems] = useState<WishlistItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [fetchError, setFetchError] = useState<string | null>(null);
    const [removedIds, setRemovedIds] = useState<Set<number>>(new Set());
    const [pendingIds, setPendingIds] = useState<Set<number>>(new Set());
    const [currentPage, setCurrentPage] = useState(1);

    // ─── 위시리스트 조회 (back: GET /wishlist) ───
    useEffect(() => {
        setIsLoading(true);
        fetchWishlist()
            .then(setItems)
            .catch((err: Error) => setFetchError(err.message))
            .finally(() => setIsLoading(false));
    }, []);

    // ─── 페이지네이션 계산 ───
    const totalPages = Math.ceil(items.length / PAGE_SIZE);
    const pageItems = items.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

    const goToPage = (page: number) => {
        setCurrentPage(page);
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    // ─── 하트 토글 (삭제 ↔ 추가) ───
    const handleToggle = async (item: WishlistItem, e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();

        if (pendingIds.has(item.wish_id)) return;

        setPendingIds((prev) => new Set(prev).add(item.wish_id));

        if (removedIds.has(item.wish_id)) {
            // 회색 하트 → 다시 추가
            try {
                const newItem = await addToWishlist({
                    user_id: item.user_id,
                    product_vector_id: item.product_vector_id,
                    product_name: item.product_name,
                    message_id: item.message_id,
                    product_description: item.product_description,
                });
                // wish_id 갱신 + removedIds에서 제거
                setItems((prev) => prev.map((i) => i.wish_id === item.wish_id ? { ...i, wish_id: newItem.wish_id } : i));
                setRemovedIds((prev) => { const next = new Set(prev); next.delete(item.wish_id); return next; });
                setPendingIds((prev) => { const next = new Set(prev); next.delete(newItem.wish_id); return next; });
            } catch (err) {
                console.error("위시리스트 추가 실패:", err);
                setPendingIds((prev) => { const next = new Set(prev); next.delete(item.wish_id); return next; });
            }
        } else {
            // 초록 하트 → 삭제
            try {
                await removeFromWishlist(item.wish_id);
                setRemovedIds((prev) => new Set(prev).add(item.wish_id));
            } catch (err) {
                console.error("위시리스트 삭제 실패:", err);
            } finally {
                setPendingIds((prev) => { const next = new Set(prev); next.delete(item.wish_id); return next; });
            }
        }
    };

    if (isLoading) return <Loading />;

    return (
        <div className="h-full overflow-y-auto bg-[#F8FBF3]">
            <div className="max-w-5xl mx-auto px-4 py-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-gray-900 font-bold">위시리스트</h1>
                        <p className="text-sm text-gray-500 mt-0.5">AI가 추천한 내 피부 맞춤 제품</p>
                    </div>
                    {!fetchError && (
                        <span className="px-3 py-1.5 rounded-xl text-sm font-semibold text-white bg-onyou">{items.length}개 저장됨</span>
                    )}
                </div>

                {/* 에러 */}
                {fetchError && (
                    <div className="py-10 text-center text-sm text-red-500">{fetchError}</div>
                )}

                {/* 빈 목록 */}
                {!fetchError && items.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-gray-400">
                        <PackageOpen className="w-14 h-14 mb-3 opacity-40" />
                        <p className="text-sm font-medium">저장된 제품이 없습니다</p>
                        <p className="text-xs mt-1">AI 채팅에서 추천받은 제품을 저장해보세요</p>
                    </div>
                )}

                {/* 목록 */}
                {!fetchError && items.length > 0 && (
                    <>
                        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                            {pageItems.map((item, idx) => (
                                <motion.div
                                    key={item.wish_id}
                                    initial={{ opacity: 0, x: -12 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ duration: 0.25, delay: idx * 0.04 }}
                                    className={idx < pageItems.length - 1 ? "border-b border-gray-50" : ""}
                                >
                                    <div className="flex items-center gap-3 px-4 py-3.5">
                                        {/* 하트 버튼 */}
                                        <button
                                            onClick={(e) => handleToggle(item, e)}
                                            disabled={pendingIds.has(item.wish_id)}
                                            className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-all cursor-pointer disabled:opacity-40 ${removedIds.has(item.wish_id) ? "bg-gray-100 hover:bg-[#E8F5D0]" : "bg-[#E8F5D0] hover:bg-red-50"}`}
                                        >
                                            {pendingIds.has(item.wish_id)
                                                ? <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                                                : <Heart className={`w-4 h-4 transition-colors ${removedIds.has(item.wish_id) ? "text-gray-300 fill-gray-300" : "text-onyou fill-onyou"}`} />
                                            }
                                        </button>

                                        {/* 제목 + 추가일 + ExternalLink */}
                                        <a
                                            href={item.product_description ?? undefined}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className={`flex flex-1 items-center min-w-0 gap-2 group ${item.product_description ? "cursor-pointer" : "cursor-default"}`}
                                        >
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-gray-800 truncate group-hover:text-onyou transition-colors">
                                                    {item.product_name}
                                                </p>
                                                <p className="text-xs text-gray-400 mt-0.5">{formatDate(item.added_at)}</p>
                                            </div>
                                            <ExternalLink className="w-4 h-4 flex-shrink-0 text-gray-300 group-hover:text-onyou transition-colors" />
                                        </a>
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        {/* 페이지네이션 */}
                        {totalPages > 1 && (
                            <div className="flex items-center justify-center gap-1 mt-6">
                                <button
                                    onClick={() => goToPage(currentPage - 1)}
                                    disabled={currentPage === 1}
                                    className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-onyou hover:bg-[#E8F5D0] disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>

                                {getPageNumbers(currentPage, totalPages).map((p, i) =>
                                    p === "..." ? (
                                        <span key={`ellipsis-${i}`} className="w-8 h-8 flex items-center justify-center text-xs text-gray-400">
                                            ···
                                        </span>
                                    ) : (
                                        <button
                                            key={p}
                                            onClick={() => goToPage(p)}
                                            className={`w-8 h-8 flex items-center justify-center rounded-lg text-xs font-medium transition-all cursor-pointer ${
                                                currentPage === p
                                                    ? "bg-onyou text-white"
                                                    : "text-gray-500 hover:text-onyou hover:bg-[#E8F5D0]"
                                            }`}
                                        >
                                            {p}
                                        </button>
                                    )
                                )}

                                <button
                                    onClick={() => goToPage(currentPage + 1)}
                                    disabled={currentPage === totalPages}
                                    className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-onyou hover:bg-[#E8F5D0] disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}