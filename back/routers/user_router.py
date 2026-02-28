"""
user_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    POST   /users/signup          회원가입 (local)
    POST   /users/login           로그인 (local)
    GET    /users/me              내 정보 조회
    PATCH  /users/me              내 정보 수정
    DELETE /users/me              회원 탈퇴
    GET    /users/check/email     이메일 중복 확인
    GET    /users/check/nickname  닉네임 중복 확인
─────────────────────────────────────────────────────────────
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from db.schemas import UserCreate, UserUpdate, UserResponse
from services import user_service
from .deps import get_current_user_id, create_access_token

router = APIRouter(prefix="/users", tags=["Users"])


# ─────────────────────────────────────────────
# 요청 바디 모델 (router 전용)
# ─────────────────────────────────────────────

class SignupRequest(BaseModel):
    """ 회원가입 요청: 사용자 정보 + 비밀번호 """
    email          : str
    name           : str
    nickname       : str
    password       : str
    terms_agreed   : bool
    privacy_agreed : bool


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

    프론트 요청 예시:
        POST /users/signup
        {
            "email": "test@test.com",
            "name": "홍길동",
            "nickname": "길동이",
            "password": "pass1234!",
            "terms_agreed": true,
            "privacy_agreed": true
        }
    """
    try:
        user_data = UserCreate(
            email          = body.email,
            name           = body.name,
            nickname       = body.nickname,
            terms_agreed   = body.terms_agreed,
            privacy_agreed = body.privacy_agreed,
        )
        user = user_service.create_user(user_data)
        user_service.register_local_auth(user.user_id, user.email, body.password)
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
        user = user_service.login_local(body.email, body.password)
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


@router.get("/check/nickname")
def check_nickname(nickname: str):
    """
    닉네임 중복 확인.

    프론트 요청 예시:
        GET /users/check/nickname?nickname=길동이
    응답:
        { "available": true }
    """
    return {"available": not user_service.is_nickname_taken(nickname)}


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

