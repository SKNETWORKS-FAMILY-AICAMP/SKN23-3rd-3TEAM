const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";


// ─────────────────────────────────────────────
// 이메일 인증 / 회원가입 / 비밀번호 재설정
// ─────────────────────────────────────────────

export interface SignupBody {
  email             : string;
  name              : string;
  nickname          : string;
  password          : string;
  terms_agreed      : boolean;
  privacy_agreed    : boolean;
  verification_code : string;
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
