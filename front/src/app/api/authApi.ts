/**
 * authApi.ts
 * ─────────────────────────────────────────────────────────────
 * 인증 관련 fetch 함수 모음.
 *
 * 사용하는 엔드포인트:
 *   POST /users/login               → login()
 *   POST /users/signup              → signup()
 *   POST /users/email/send-code     → sendEmailCode()
 *   POST /users/email/verify-code   → verifyEmailCode()
 *   POST /users/password/reset      → resetPassword()
 * ─────────────────────────────────────────────────────────────
 */

import type { UserResponse } from "./userApi";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// ─────────────────────────────────────────────
// 소셜 로그인
// ─────────────────────────────────────────────

/**
 * 소셜 로그인 시작 — 브라우저를 백엔드 OAuth URL로 이동시킨다.
 * 백엔드가 Google/Kakao 인증 페이지로 리디렉션하고,
 * 인증 완료 후 /oauth/callback?token=<jwt> 로 돌아온다.
 * back: GET /auth/{provider}/login
 */
export function startSocialLogin(provider: "google" | "kakao" | "naver"): void {
  window.location.href = `${API_BASE}/auth/${provider}/login`;
}

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────

/** back/routers/user_router.py SignupRequest 대응 */
export interface SignupBody {
  email             : string;
  name              : string;
  nickname          : string;
  password          : string;
  terms_agreed      : boolean;
  privacy_agreed    : boolean;
  verification_code : string;
}

// ─────────────────────────────────────────────
// 로그인 / 로그아웃 / 회원가입
// ─────────────────────────────────────────────

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
  clearGuestData();
}

/** 로그아웃 — localStorage에서 토큰 제거. */
export function logout(): void {
  localStorage.removeItem("access_token");
}

/** 비회원 채팅 데이터 초기화 — 로그인/회원가입 성공 시 호출. */
function clearGuestData(): void {
  localStorage.removeItem("guest_chats");
  localStorage.removeItem("guest_chat_count");
}

/**
 * 회원가입 (local).
 * back: POST /users/signup → user_service.create_user() + register_local_auth()
 */
export async function signup(body: SignupBody): Promise<UserResponse> {
  const res = await fetch(`${API_BASE}/users/signup`, {
    method  : "POST",
    headers : { "Content-Type": "application/json" },
    body    : JSON.stringify(body),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `가입 실패 (${res.status})`);
  }

  return res.json() as Promise<UserResponse>;
}

// ─────────────────────────────────────────────
// 이메일 OTP 인증
// ─────────────────────────────────────────────

/**
 * 이메일 인증 코드 발송.
 * back: POST /users/email/send-code → email_service.send_verification_email()
 */
export async function sendEmailCode(email: string): Promise<void> {
  const res = await fetch(`${API_BASE}/users/email/send-code`, {
    method  : "POST",
    headers : { "Content-Type": "application/json" },
    body    : JSON.stringify({ email }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `발송 실패 (${res.status})`);
  }
}

/**
 * 이메일 인증 코드 확인.
 * back: POST /users/email/verify-code → email_service.verify_otp()
 * @returns true면 코드 일치, false면 불일치/만료
 */
export async function verifyEmailCode(email: string, code: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/users/email/verify-code`, {
    method  : "POST",
    headers : { "Content-Type": "application/json" },
    body    : JSON.stringify({ email, code }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `확인 실패 (${res.status})`);
  }

  const data = await res.json() as { valid: boolean };
  return data.valid;
}

/**
 * 비밀번호 재설정.
 * back: POST /users/password/reset → user_service.reset_password()
 */
export async function resetPassword(
  email       : string,
  code        : string,
  newPassword : string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/users/password/reset`, {
    method  : "POST",
    headers : { "Content-Type": "application/json" },
    body    : JSON.stringify({ email, code, new_password: newPassword }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `재설정 실패 (${res.status})`);
  }
}
