/**
 * wishlistApi.ts
 * ─────────────────────────────────────────────────────────────
 * back/routers/wishlist_router.py 의 /wishlist 엔드포인트와 통신.
 *
 * 사용하는 엔드포인트:
 *   GET    /wishlist              → fetchWishlist()
 *   POST   /wishlist              → addToWishlist()
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
// 타입 정의
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
export interface WishlistAddBody {
    user_id             : number;
    product_vector_id   : string;
    product_name        : string;
    message_id         ?: number | null;
    product_description?: string | null;
}

// ─────────────────────────────────────────────
// API 호출 함수
// ─────────────────────────────────────────────

/**
 * 내 위시리스트 전체 조회. (최신순)
 * 
 * GET /wishlist
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
 * 위시리스트에 제품 추가.
 * 
 * POST /wishlist
 */
export async function addToWishlist(body: WishlistAddBody): Promise<WishlistItem> {
    const res = await fetch(`${API_BASE}/wishlist`, {
        method : "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization : `Bearer ${getToken()}`,
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const msg = (data as { detail?: string }).detail ?? `서버 오류 (${res.status})`;

        throw Object.assign(new Error(msg), { statusCode: res.status });
    }

    return res.json() as Promise<WishlistItem>;
}

/**
 * 위시리스트 항목 삭제.
 * 
 * DELETE /wishlist/{wish_id}
 */
export async function removeFromWishlist(wishId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/wishlist/${wishId}`, {
        method  : "DELETE",
        headers : { Authorization: `Bearer ${getToken()}` },
    });

    if (!res.ok && res.status !== 204) {    // 204 No Content = 정상 삭제
        const data = await res.json().catch(() => ({}));

        throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
    }
}
