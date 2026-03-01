"""
schemas.py
─────────────────────────────────────────────────────────────
목적  : 프론트 ↔ 백 데이터 계약 (입출력 검증)
역할  :
    - 프론트에서 받은 데이터 유효성 검증 (Pydantic)
    - API 응답 데이터 형태 정의
    - model_type, provider_type 등 허용값 제한

구성:
    [User]           UserCreate / UserUpdate / UserResponse
    [AuthProvider]   AuthProviderCreate / LoginRequest / AuthResponse
    [ChatRoom]       ChatRoomCreate / ChatRoomResponse
    [ChatMessage]    MessageCreate / MessageResponse
    [Analysis]       AnalysisCreate / AnalysisResponse
    [Wishlist]       WishlistAdd / WishlistResponse
─────────────────────────────────────────────────────────────
"""

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime


# ─────────────────────────────────────────────
# 1. User 스키마
# ─────────────────────────────────────────────

class UserCreate(BaseModel):
    """
    회원가입 시 프론트에서 받는 데이터
    - 이메일 형식 자동 검증 (EmailStr)
    - 약관 동의 필수 검증
    """
    email          : EmailStr
    name           : str
    nickname       : str
    terms_agreed   : bool
    privacy_agreed : bool

    @model_validator(mode="after")
    def check_terms(self) -> "UserCreate":
        """ 필수 약관 미동의 시 가입 차단 """
        if not self.terms_agreed:
            raise ValueError("서비스 이용약관 동의는 필수입니다.")
        if not self.privacy_agreed:
            raise ValueError("개인정보 처리방침 동의는 필수입니다.")
        return self


class UserUpdate(BaseModel):
    """
    프로필 수정 시 프론트에서 받는 데이터
    - 모든 필드 선택적 (수정할 항목만 전달)
    """
    nickname          : Optional[str] = None
    age               : Optional[int] = None
    gender            : Optional[Literal["male", "female"]] = None
    skin_type         : Optional[int] = None   # keywords.keyword_id
    skin_concern      : Optional[str] = None
    profile_image_url : Optional[str] = None   # S3 URL


class UserResponse(BaseModel):
    """
    API 응답으로 내보내는 사용자 데이터
    - 비밀번호 등 민감 정보 제외
    """
    user_id           : int
    email             : str
    name              : str
    nickname          : str
    age               : Optional[int]      = None
    gender            : Optional[str]      = None
    skin_type         : Optional[int]      = None
    skin_concern      : Optional[str]      = None
    profile_image_url : Optional[str]      = None
    is_active         : bool
    created_at        : datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 2. AuthProvider 스키마
# ─────────────────────────────────────────────

class AuthProviderCreate(BaseModel):
    """
    로그인 수단 등록 시 데이터
    - provider_type: local / google / kakao 만 허용
    - local일 경우 password_hash 필수
    """
    user_id       : int
    provider_type : Literal["local", "google", "kakao"]
    provider_id   : str                    # local이면 이메일, 소셜이면 소셜 고유 ID
    password_hash : Optional[str] = None  # local 전용

    @model_validator(mode="after")
    def check_password(self) -> "AuthProviderCreate":
        """ local 로그인인데 비밀번호 해시가 없으면 차단 """
        if self.provider_type == "local" and not self.password_hash:
            raise ValueError("local 로그인은 password_hash가 필요합니다.")
        return self


class LoginRequest(BaseModel):
    """
    로컬 로그인 요청 시 프론트에서 받는 데이터
    """
    email    : EmailStr
    password : str


class AuthResponse(BaseModel):
    """
    로그인 수단 조회 응답
    - password_hash 제외하고 반환
    """
    auth_id       : int
    user_id       : int
    provider_type : str
    provider_id   : str
    created_at    : datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 3. ChatRoom 스키마
# ─────────────────────────────────────────────

class ChatRoomCreate(BaseModel):
    """
    채팅방 생성 시 프론트에서 받는 데이터
    - title은 생략 가능 (첫 질문 요약 후 서버에서 설정)
    """
    user_id : int
    title   : Optional[str] = None


class ChatRoomResponse(BaseModel):
    """
    채팅방 조회 응답
    """
    chat_room_id : int
    user_id      : int
    title        : Optional[str]      = None
    created_at   : Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 4. ChatMessage 스키마
# ─────────────────────────────────────────────

class MessageCreate(BaseModel):
    """
    메시지 저장 시 프론트에서 받는 데이터
    - role: user / assistant / system 만 허용
    - model_type: simple / detailed 만 허용
    - content와 image_url 중 하나는 반드시 있어야 함
    """
    chat_room_id : int
    role         : Literal["user", "assistant", "system"]
    model_type   : Literal["simple", "detailed", "ingredient"]
    content      : Optional[str]       = None  # 텍스트 메시지
    image_url    : Optional[list[str]] = None  # S3 이미지 URL 배열

    @model_validator(mode="after")
    def check_content_or_image(self) -> "MessageCreate":
        """ 텍스트도 없고 이미지도 없으면 차단 """
        if not self.content and not self.image_url:
            raise ValueError("content 또는 image_url 중 하나는 필수입니다.")
        return self


class MessageResponse(BaseModel):
    """
    메시지 조회 응답
    """
    message_id   : int
    chat_room_id : int
    role         : str
    model_type   : str
    content      : Optional[str]       = None
    image_url    : Optional[list[str]] = None
    created_at   : Optional[datetime]  = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 5. SkinAnalysisResult 스키마
# ─────────────────────────────────────────────

class AnalysisCreate(BaseModel):
    """
    피부 분석 결과 저장 시 데이터
    - model_type: simple / detailed 만 허용
    - image_url: 분석에 사용된 S3 이미지 URL 배열
    - analysis_data: AI 분석 결과 구조화 데이터 (dict)
    """
    user_id       : int
    image_url     : list[str]          # S3 URL 배열 (simple: 1장, detailed: 3장)
    model_type    : Literal["simple", "detailed"]
    analysis_data : dict               # 정량 분석 결과 JSON

    @field_validator("image_url")
    @classmethod
    def check_image_count(cls, v: list[str]) -> list[str]:
        """ 이미지 URL이 비어있으면 차단 """
        if not v:
            raise ValueError("image_url은 최소 1개 이상이어야 합니다.")
        return v


class AnalysisResponse(BaseModel):
    """
    피부 분석 결과 조회 응답
    """
    analysis_id   : int
    user_id       : int
    image_url     : list[str]
    model_type    : str
    analysis_data : dict
    created_at    : datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 6. Wishlist 스키마
# ─────────────────────────────────────────────

class WishlistAdd(BaseModel):
    """
    위시리스트 추가 시 프론트에서 받는 데이터
    """
    user_id             : int
    product_vector_id   : str            # 벡터DB 제품 고유 ID
    product_name        : str            # 제품명
    message_id          : Optional[int] = None  # 추천한 메시지 ID
    product_description : Optional[str] = None  # 제품 간단 설명


class WishlistResponse(BaseModel):
    """
    위시리스트 조회 응답
    """
    wish_id             : int
    user_id             : int
    product_vector_id   : str
    product_name        : str
    product_description : Optional[str]  = None
    message_id          : Optional[int]  = None
    added_at            : datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 7. 이메일 인증 스키마
# ─────────────────────────────────────────────

class EmailSendRequest(BaseModel):
    """
    이메일 인증 코드 발송 요청
    - 회원가입 / 비밀번호 찾기 모두 공통 사용
    """
    email : EmailStr


class EmailVerifyRequest(BaseModel):
    """
    이메일 인증 코드 확인 요청
    """
    email : EmailStr
    code  : str


class PasswordResetRequest(BaseModel):
    """
    비밀번호 재설정 요청
    - OTP 검증 후 새 비밀번호로 변경
    """
    email        : EmailStr
    code         : str
    new_password : str


# ─────────────────────────────────────────────
# 8. Keyword 스키마
# ─────────────────────────────────────────────

class KeywordResponse(BaseModel):
    """
    키워드 조회 응답
    - skin_type, gender 등 공통 코드 테이블
    """
    keyword_id  : int
    type        : str
    keyword     : str
    label       : Optional[str] = None
    description : Optional[str] = None

    model_config = {"from_attributes": True}