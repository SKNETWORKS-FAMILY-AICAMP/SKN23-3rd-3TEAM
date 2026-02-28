"""
models.py
─────────────────────────────────────────────────────────────
목적  : 각 테이블의 데이터 구조를 Python dataclass로 정의
역할  :
    - DB에서 조회한 raw dict 데이터를 타입이 있는 객체로 변환
    - services 에서 데이터를 다룰 때 타입 안전성 확보
    - DB 저장용이 아닌 '데이터 표현' 용도 (ORM 아님)

포함 테이블:
    Keyword / User / AuthProvider / ChatRoom
    ChatMessage / SkinAnalysisResult / Wishlist
─────────────────────────────────────────────────────────────
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
# 1. Keyword
# 테이블: keywords
# 역할  : 피부타입/성별 등 공통 코드 (enum 역할)
# ─────────────────────────────────────────────
@dataclass
class Keyword:
    keyword_id  : int
    type        : str                    # 키워드 그룹 (예: skin_type, gender)
    keyword     : str                    # 코드 내부 값 (예: dry, oily)
    label       : Optional[str] = None  # 화면 표시 이름 (예: 건성, 지성)
    description : Optional[str] = None  # 설명

    @staticmethod
    def from_dict(row: dict) -> "Keyword":
        """ DB 조회 결과 dict → Keyword 객체 변환 """
        return Keyword(
            keyword_id  = row["keyword_id"],
            type        = row["type"],
            keyword     = row["keyword"],
            label       = row.get("label"),
            description = row.get("description"),
        )


# ─────────────────────────────────────────────
# 2. User
# 테이블: users
# 역할  : 서비스 사용자 기본 정보
# ─────────────────────────────────────────────
@dataclass
class User:
    user_id           : int
    email             : str
    name              : str
    nickname          : str
    is_email_verified : bool
    is_active         : bool
    terms_agreed      : bool
    privacy_agreed    : bool
    created_at        : datetime
    updated_at        : datetime
    profile_image_url : Optional[str]      = None  # S3 프로필 이미지 URL
    age               : Optional[int]      = None
    gender            : Optional[str]      = None  # male / female
    skin_type         : Optional[int]      = None  # FK → keywords.keyword_id
    skin_concern      : Optional[str]      = None  # 피부 고민 (트러블, 주름 등)
    deleted_at        : Optional[datetime] = None  # soft delete 시각

    @staticmethod
    def from_dict(row: dict) -> "User":
        """ DB 조회 결과 dict → User 객체 변환 """
        return User(
            user_id           = row["user_id"],
            email             = row["email"],
            name              = row["name"],
            nickname          = row["nickname"],
            is_email_verified = bool(row["is_email_verified"]),
            is_active         = bool(row["is_active"]),
            terms_agreed      = bool(row["terms_agreed"]),
            privacy_agreed    = bool(row["privacy_agreed"]),
            created_at        = row["created_at"],
            updated_at        = row["updated_at"],
            profile_image_url = row.get("profile_image_url"),
            age               = row.get("age"),
            gender            = row.get("gender"),
            skin_type         = row.get("skin_type"),
            skin_concern      = row.get("skin_concern"),
            deleted_at        = row.get("deleted_at"),
        )


# ─────────────────────────────────────────────
# 3. AuthProvider
# 테이블: auth_providers
# 역할  : 사용자 로그인 수단 관리 (local / google / kakao)
# ─────────────────────────────────────────────
@dataclass
class AuthProvider:
    auth_id       : int
    user_id       : int
    provider_type : str                    # local / google / kakao
    provider_id   : str                    # 각 provider의 고유 사용자 ID
    created_at    : datetime
    password_hash : Optional[str] = None  # local 로그인 전용 (소셜이면 None)

    @staticmethod
    def from_dict(row: dict) -> "AuthProvider":
        """ DB 조회 결과 dict → AuthProvider 객체 변환 """
        return AuthProvider(
            auth_id       = row["auth_id"],
            user_id       = row["user_id"],
            provider_type = row["provider_type"],
            provider_id   = row["provider_id"],
            created_at    = row["created_at"],
            password_hash = row.get("password_hash"),
        )


# ─────────────────────────────────────────────
# 4. ChatRoom
# 테이블: chat_rooms
# 역할  : 사용자별 채팅 세션 단위
# ─────────────────────────────────────────────
@dataclass
class ChatRoom:
    chat_room_id : int
    user_id      : int
    title        : Optional[str]      = None  # 첫 질문 요약 제목
    created_at   : Optional[datetime] = None
    deleted_at   : Optional[datetime] = None  # soft delete 시각

    @staticmethod
    def from_dict(row: dict) -> "ChatRoom":
        """ DB 조회 결과 dict → ChatRoom 객체 변환 """
        return ChatRoom(
            chat_room_id = row["chat_room_id"],
            user_id      = row["user_id"],
            title        = row.get("title"),
            created_at   = row.get("created_at"),
            deleted_at   = row.get("deleted_at"),
        )


# ─────────────────────────────────────────────
# 5. ChatMessage
# 테이블: chat_messages
# 역할  : 채팅방 내 메시지 (user / assistant / system)
# ─────────────────────────────────────────────
@dataclass
class ChatMessage:
    message_id   : int
    chat_room_id : int
    role         : str                     # user / assistant / system
    model_type   : str                     # simple / detailed
    content      : Optional[str]      = None  # 텍스트 내용 (이미지 전용이면 None)
    image_url    : Optional[list]     = None  # S3 이미지 URL 배열 (JSON)
    created_at   : Optional[datetime] = None

    @staticmethod
    def from_dict(row: dict) -> "ChatMessage":
        """ DB 조회 결과 dict → ChatMessage 객체 변환 """
        img_url = row.get("image_url")

        return ChatMessage(
            message_id   = row["message_id"],
            chat_room_id = row["chat_room_id"],
            role         = row["role"],
            model_type   = row["model_type"],
            content      = row.get("content"),
            image_url    = img_url.split(",") if img_url else [],
            created_at   = row.get("created_at"),
        )


# ─────────────────────────────────────────────
# 6. SkinAnalysisResult
# 테이블: skin_analysis_results
# 역할  : AI 피부 분석 결과 저장
# ─────────────────────────────────────────────
@dataclass
class SkinAnalysisResult:
    analysis_id   : int
    user_id       : int
    image_url     : list    # 분석에 사용된 S3 이미지 URL 배열 (JSON)
    model_type    : str     # simple / detailed
    analysis_data : dict    # 피부 분석 구조화 데이터 (정량 지표 등, JSON)
    created_at    : datetime
    deleted_at    : Optional[datetime] = None  # soft delete 시각

    @staticmethod
    def from_dict(row: dict) -> "SkinAnalysisResult":
        """ DB 조회 결과 dict → SkinAnalysisResult 객체 변환 """
        return SkinAnalysisResult(
            analysis_id   = row["analysis_id"],
            user_id       = row["user_id"],
            image_url     = row["image_url"],      # pymysql이 JSON을 자동 파싱
            model_type    = row["model_type"],
            analysis_data = row["analysis_data"],  # pymysql이 JSON을 자동 파싱
            created_at    = row["created_at"],
            deleted_at    = row.get("deleted_at"),
        )


# ─────────────────────────────────────────────
# 7. Wishlist
# 테이블: wishlist
# 역할  : 사용자가 추천받은 제품 중 저장한 목록
# ─────────────────────────────────────────────
@dataclass
class Wishlist:
    wish_id             : int
    user_id             : int
    product_vector_id   : str                    # 벡터DB 제품 고유 ID
    product_name        : str                    # 제품명 (화면 표시용)
    added_at            : datetime
    message_id          : Optional[int]  = None  # 추천한 assistant 메시지 ID (삭제되면 None)
    product_description : Optional[str]  = None  # 제품 간단 설명

    @staticmethod
    def from_dict(row: dict) -> "Wishlist":
        """ DB 조회 결과 dict → Wishlist 객체 변환 """
        return Wishlist(
            wish_id             = row["wish_id"],
            user_id             = row["user_id"],
            product_vector_id   = row["product_vector_id"],
            product_name        = row["product_name"],
            added_at            = row["added_at"],
            message_id          = row.get("message_id"),
            product_description = row.get("product_description"),
        )