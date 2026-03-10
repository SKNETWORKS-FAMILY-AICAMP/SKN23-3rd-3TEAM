/**
 * userApi.ts
 * ─────────────────────────────────────────────────────────────
 * 사용자 정보 / 키워드 관련 fetch 함수 모음.
 *
 * 사용하는 엔드포인트:
 *   GET   /users/me   → fetchCurrentUser()
 *   PATCH /users/me   → updateCurrentUser()
 *   GET   /keywords   → fetchKeywords()
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

export interface UserResponse {
    user_id           : number;
    email             : string;
    name              : string;
    nickname          : string;
    age               : number | null;
    gender            : "male" | "female" | null;
    skin_type         : number | null;
    skin_concern      : string | null;
    profile_image_url : string | null;
    is_active         : boolean;
    created_at        : string;
}
export interface UserUpdateBody {
    nickname          ?: string;
    age               ?: number | null;
    gender            ?: "male" | "female" | null;
    skin_type         ?: number | null;
    skin_concern      ?: string | null;
    profile_image_url ?: string | null;
}
export interface KeywordItem {
    keyword_id  : number;
    type        : string;
    keyword     : string;
    label       : string | null;
    description : string | null;
}
export interface SocialLinksResponse {
    is_social : boolean;
    providers : string[];
}

// ─────────────────────────────────────────────
// API 호출 함수
// ─────────────────────────────────────────────

/**
 * 로그인한 사용자 정보 조회.
 * 
 * GET /users/me
 */
export async function fetchCurrentUser(): Promise<UserResponse> {
    const res = await fetch(`${API_BASE}/users/me`, {
        headers: { Authorization: `Bearer ${getToken()}` },
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));

        throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
    }

    return res.json() as Promise<UserResponse>;
}

/**
 * 프로필 수정.
 * 
 * PATCH /users/me
 */
export async function updateCurrentUser(body: UserUpdateBody): Promise<UserResponse> {
    const res = await fetch(`${API_BASE}/users/me`, {
        method  : "PATCH",
        headers : {
            "Content-Type" : "application/json",
            Authorization  : `Bearer ${getToken()}`,
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));

        throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
    }

    return res.json() as Promise<UserResponse>;
}

/**
 * 내 소셜 연동 계정 조회.
 * 
 * GET /users/me/social-links
 */
export async function fetchSocialLinks(): Promise<SocialLinksResponse> {
    const res = await fetch(`${API_BASE}/users/me/social-links`, {
        headers: { Authorization: `Bearer ${getToken()}` },
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));

        throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
    }

    return res.json() as Promise<SocialLinksResponse>;
}

/**
 * 키워드 목록 조회. (인증 불필요)
 * 
 * GET /keywords?type={type}
 *
 * @param type  필터링할 키워드 타입 (예: "skin_type"). 생략 시 전체 반환.
 */
export async function fetchKeywords(type?: string): Promise<KeywordItem[]> {
    const url = type
        ? `${API_BASE}/keywords?type=${encodeURIComponent(type)}`
        : `${API_BASE}/keywords`;

    const res = await fetch(url);

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        
        throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
    }

    return res.json() as Promise<KeywordItem[]>;
}
