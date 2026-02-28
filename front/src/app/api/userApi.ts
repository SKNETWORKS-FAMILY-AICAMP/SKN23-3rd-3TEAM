/**
 * userApi.ts
 * ─────────────────────────────────────────────────────────────
 * back/routers/user_router.py 의 /users 엔드포인트와 통신하는 fetch 함수 모음.
 *
 * 사용하는 엔드포인트:
 *   GET  /users/me   → fetchCurrentUser()   (user_service.get_user_by_id)
 *   PATCH /users/me  → updateCurrentUser()  (user_service.update_user)
 * ─────────────────────────────────────────────────────────────
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/** localStorage에서 JWT access_token 읽기 */
function getToken(): string {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("로그인이 필요합니다.");
  return token;
}

/** 타입 정의 (back/db/schemas.py UserResponse 대응) */
export interface UserResponse {
  user_id           : number;
  email             : string;
  name              : string;
  nickname          : string;
  age               : number | null;
  gender            : "male" | "female";
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

/**
 * 로컬 이메일/비밀번호 로그인.
 * back: POST /users/login → create_access_token()
 * 성공 시 access_token을 localStorage에 저장.
 */
export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/users/login`, {
    method  : "POST",
    headers : { "Content-Type": "application/json" },
    body    : JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `로그인 실패 (${res.status})`);
  }

  const data = await res.json() as { access_token: string };
  localStorage.setItem("access_token", data.access_token);
}

/**
 * 로그아웃 — localStorage에서 토큰 제거.
 */
export function logout(): void {
  localStorage.removeItem("access_token");
}

/**
 * 로그인한 사용자 정보 조회.
 * back: GET /users/me → user_service.get_user_by_id(user_id)
 *
 * @throws Error  토큰 없음(401) 또는 서버 오류
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
 * back: PATCH /users/me → user_service.update_user(user_id, data)
 * 변경할 필드만 담아서 전달.
 *
 * @throws Error  유효성 오류(400) 또는 서버 오류
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
