/**
 * wishlistApi.ts
 * ─────────────────────────────────────────────────────────────
 * back/routers/wishlist_router.py 의 /wishlist 엔드포인트와 통신.
 *
 * 사용하는 엔드포인트:
 *   GET    /wishlist              → fetchWishlist()
 *   DELETE /wishlist/{wish_id}    → removeFromWishlist()
 * ─────────────────────────────────────────────────────────────
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function getToken(): string {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("로그인이 필요합니다.");
  return token;
}

// ─────────────────────────────────────────────
// 타입 정의 (back/db/schemas.py WishlistResponse 대응)
// ─────────────────────────────────────────────

export interface WishlistItem {
  wish_id             : number;
  user_id             : number;
  product_vector_id   : string;
  product_name        : string;
  product_description : string | null;
  message_id          : number | null;
  added_at            : string;
}

// ─────────────────────────────────────────────
// API 함수
// ─────────────────────────────────────────────

/**
 * 내 위시리스트 전체 조회 (최신순).
 * back: GET /wishlist → analysis_service.get_wishlist_by_user()
 */
export async function fetchWishlist(): Promise<WishlistItem[]> {
  const res = await fetch(`${API_BASE}/wishlist`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }

  return res.json() as Promise<WishlistItem[]>;
}

/**
 * 위시리스트 단건 조회.
 * back: GET /wishlist/{wish_id} → analysis_service.get_wishlist_item_by_id()
 */
export async function fetchWishlistItem(wishId: number): Promise<WishlistItem> {
  const res = await fetch(`${API_BASE}/wishlist/${wishId}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }

  return res.json() as Promise<WishlistItem>;
}

/**
 * 위시리스트 항목 삭제.
 * back: DELETE /wishlist/{wish_id} → analysis_service.remove_from_wishlist()
 */
export async function removeFromWishlist(wishId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/wishlist/${wishId}`, {
    method  : "DELETE",
    headers : { Authorization: `Bearer ${getToken()}` },
  });

  // 204 No Content = 정상 삭제
  if (!res.ok && res.status !== 204) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
}
