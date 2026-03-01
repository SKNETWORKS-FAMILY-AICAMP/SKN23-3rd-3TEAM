"""
user_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    POST   /users/signup               회원가입 (local, OTP 검증 포함)
    POST   /users/login                로그인 (local)
    GET    /users/me                   내 정보 조회
    PATCH  /users/me                   내 정보 수정
    DELETE /users/me                   회원 탈퇴
    GET    /users/check/email          이메일 중복 확인
    POST   /users/email/send-code      이메일 OTP 발송
    POST   /users/email/verify-code    이메일 OTP 확인
    POST   /users/password/reset       비밀번호 재설정 (OTP 검증 포함)
─────────────────────────────────────────────────────────────
"""

import os

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from db.schemas import UserCreate, UserUpdate, UserResponse, EmailSendRequest, EmailVerifyRequest, PasswordResetRequest
from services import user_service
from services import auth_service
from services import email_service
from .deps import get_current_user_id, create_access_token

router = APIRouter(prefix="/users", tags=["Users"])


# ─────────────────────────────────────────────
# 요청 바디 모델 (router 전용)
# ─────────────────────────────────────────────

class SignupRequest(BaseModel):
    """ 회원가입 요청: 사용자 정보 + 비밀번호 + 이메일 인증 코드 """
    email               : str
    name                : str
    nickname            : str
    password            : str
    terms_agreed        : bool
    privacy_agreed      : bool
    verification_code   : str   # 이메일 OTP 인증 코드 (필수)


class LoginRequest(BaseModel):
    email    : str
    password : str


class TokenResponse(BaseModel):
    access_token : str
    token_type   : str = "bearer"


# ─────────────────────────────────────────────
# 회원가입 / 로그인
# ─────────────────────────────────────────────

@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(body: SignupRequest):
    """
    회원가입 (local 로그인 수단 포함).
    - 이메일 OTP 인증이 완료된 후 호출해야 함 (verification_code 필수)

    프론트 요청 예시:
        POST /users/signup
        {
            "email": "test@test.com",
            "name": "홍길동",
            "nickname": "길동이",
            "password": "pass1234!",
            "terms_agreed": true,
            "privacy_agreed": true,
            "verification_code": "123456"
        }
    """
    secret = os.getenv("EMAIL_OTP_SECRET", "")
    if not email_service.verify_otp(body.email, body.verification_code, secret):
        raise HTTPException(status_code=400, detail="이메일 인증 코드가 유효하지 않거나 만료되었습니다.")

    try:
        user_data = UserCreate(
            email          = body.email,
            name           = body.name,
            nickname       = body.nickname,
            terms_agreed   = body.terms_agreed,
            privacy_agreed = body.privacy_agreed,
        )
        user = user_service.create_user(user_data)
        auth_service.register_local_auth(user.user_id, user.email, body.password)
        return _to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """
    로컬 이메일/비밀번호 로그인.
    성공 시 JWT access_token 반환.

    프론트 요청 예시:
        POST /users/login
        { "email": "test@test.com", "password": "pass1234!" }
    """
    try:
        user = auth_service.login_local(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = create_access_token(user.user_id)
    return TokenResponse(access_token=token)


# ─────────────────────────────────────────────
# 내 정보
# ─────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(user_id: int = Depends(get_current_user_id)):
    """
    로그인한 사용자 본인 정보 조회.
    Authorization 헤더의 JWT에서 user_id 추출.

    프론트 요청 예시:
        GET /users/me
        Headers: { Authorization: "Bearer <token>" }
    """
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return _to_response(user)


@router.patch("/me", response_model=UserResponse)
def update_me(body: UserUpdate, user_id: int = Depends(get_current_user_id)):
    """
    프로필 수정 (수정할 필드만 전달).

    프론트 요청 예시:
        PATCH /users/me
        { "nickname": "새닉네임", "age": 25, "skin_type": 1 }
    """
    try:
        user = user_service.update_user(user_id, body)
        return _to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/me", status_code=204)
def delete_me(user_id: int = Depends(get_current_user_id)):
    """
    회원 탈퇴 (soft delete).

    프론트 요청 예시:
        DELETE /users/me
    """
    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")


# ─────────────────────────────────────────────
# 이메일 OTP 인증
# ─────────────────────────────────────────────

@router.post("/email/send-code", status_code=200)
def send_email_code(body: EmailSendRequest):
    """
    이메일 OTP 코드 발송.
    - 회원가입 / 비밀번호 찾기 모두 이 엔드포인트 사용
    - SendGrid를 통해 6자리 코드 발송

    프론트 요청 예시:
        POST /g
        { "email": "test@test.com" }
    응답:
        { "message": "인증 코드가 발송되었습니다." }
    """
    secret = os.getenv("EMAIL_OTP_SECRET", "")
    otp = email_service.generate_otp(body.email, secret)
    try:
        email_service.send_verification_email(body.email, otp)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "인증 코드가 발송되었습니다."}


@router.post("/email/verify-code", status_code=200)
def verify_email_code(body: EmailVerifyRequest):
    """
    이메일 OTP 코드 유효성 확인 (DB 저장 없음).
    - 프론트에서 코드 입력 직후 즉시 검증용
    - 회원가입 최종 요청 시에도 서버에서 재검증됨

    프론트 요청 예시:
        POST /users/email/verify-code
        { "email": "test@test.com", "code": "123456" }
    응답:
        { "valid": true }
    """
    secret = os.getenv("EMAIL_OTP_SECRET", "")
    valid = email_service.verify_otp(body.email, body.code, secret)
    return {"valid": valid}


# ─────────────────────────────────────────────
# 비밀번호 재설정
# ─────────────────────────────────────────────

@router.post("/password/reset", status_code=200)
def reset_password(body: PasswordResetRequest):
    """
    비밀번호 재설정.
    - OTP 검증 후 새 비밀번호로 변경

    프론트 요청 예시:
        POST /users/password/reset
        {
            "email": "test@test.com",
            "code": "123456",
            "new_password": "newPass1234!"
        }
    응답:
        { "message": "비밀번호가 변경되었습니다." }
    """
    secret = os.getenv("EMAIL_OTP_SECRET", "")
    if not email_service.verify_otp(body.email, body.code, secret):
        raise HTTPException(status_code=400, detail="이메일 인증 코드가 유효하지 않거나 만료되었습니다.")

    try:
        auth_service.reset_password(body.email, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "비밀번호가 변경되었습니다."}


# ─────────────────────────────────────────────
# 중복 확인
# ─────────────────────────────────────────────

@router.get("/check/email")
def check_email(email: str):
    """
    이메일 중복 확인.

    프론트 요청 예시:
        GET /users/check/email?email=test@test.com
    응답:
        { "available": true }
    """
    return {"available": not user_service.is_email_taken(email)}



# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────

def _to_response(user) -> dict:
    return UserResponse(
        user_id           = user.user_id,
        email             = user.email,
        name              = user.name,
        nickname          = user.nickname,
        age               = user.age,
        gender            = user.gender,
        skin_type         = user.skin_type,
        skin_concern      = user.skin_concern,
        profile_image_url = user.profile_image_url,
        is_active         = user.is_active,
        created_at        = user.created_at,
    )

