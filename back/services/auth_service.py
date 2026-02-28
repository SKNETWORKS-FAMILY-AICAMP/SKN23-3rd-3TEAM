"""
auth_service.py
─────────────────────────────────────────────────────────────
목적  : 인증 및 로그인 관련 비즈니스 로직 담당
역할  :
    1. local 로그인 수단 등록 (비밀번호 해시 포함)
    2. 소셜 로그인 수단 등록 (google / kakao)
    3. local 이메일/비밀번호 로그인 검증
    4. 로그인 수단 조회

흐름:
    FastAPI 라우터 → auth_service 함수 호출
                    → db_manager 헬퍼로 DB 접근
                    → models.AuthProvider / User 로 변환 후 반환

의존성:
    user_service.get_user_by_email() 호출 (단방향)
    auth_service → user_service (user_service는 auth_service를 import하지 않음)
─────────────────────────────────────────────────────────────
"""

import bcrypt
from typing import Optional

from db.db_manager import execute_one, execute_write
from db.models import AuthProvider, User
from db.schemas import AuthProviderCreate
from services.user_service import get_user_by_email


# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────

def _hash_password(plain_password: str) -> str:
    """ 평문 비밀번호 → bcrypt 해시 변환 """
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain_password: str, hashed: str) -> bool:
    """ 평문 비밀번호와 해시 일치 여부 확인 """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))


# ─────────────────────────────────────────────
# 1. 로그인 수단 등록
# ─────────────────────────────────────────────

def register_local_auth(user_id: int, email: str, plain_password: str) -> AuthProvider:
    """
    local 로그인 수단 등록.
    - 비밀번호를 bcrypt로 해시 후 auth_providers에 INSERT
    - create_user() 호출 직후 함께 사용

    사용 예시:
        from services.user_service import create_user
        from services.auth_service import register_local_auth

        user = create_user(data)
        auth = register_local_auth(user.user_id, user.email, "plain_password_123")
    """
    # 이미 등록된 local 수단이 있으면 예외 발생
    existing = execute_one(
        """
        SELECT auth_id FROM auth_providers
        WHERE user_id = %s AND provider_type = 'local'
        """,
        (user_id,)
    )
    if existing:
        raise ValueError("이미 local 로그인 수단이 등록된 계정입니다.")

    hashed = _hash_password(plain_password)
    auth_data = AuthProviderCreate(
        user_id       = user_id,
        provider_type = "local",
        provider_id   = email,
        password_hash = hashed,
    )
    auth_id = execute_write(
        """
        INSERT INTO auth_providers (user_id, provider_type, provider_id, password_hash)
        VALUES (%s, %s, %s, %s)
        """,
        (auth_data.user_id, auth_data.provider_type, auth_data.provider_id, auth_data.password_hash)
    )
    return get_auth_by_id(auth_id)


def register_social_auth(user_id: int, provider_type: str, provider_id: str) -> AuthProvider:
    """
    소셜 로그인 수단 등록 (google / kakao).
    - 이미 연결된 소셜 계정이면 예외 발생

    사용 예시:
        auth = register_social_auth(user.user_id, "google", "google_uid_abc123")
    """
    existing = execute_one(
        """
        SELECT auth_id FROM auth_providers
        WHERE provider_type = %s AND provider_id = %s
        """,
        (provider_type, provider_id)
    )
    if existing:
        raise ValueError(f"이미 연결된 {provider_type} 계정입니다.")

    auth_id = execute_write(
        """
        INSERT INTO auth_providers (user_id, provider_type, provider_id)
        VALUES (%s, %s, %s)
        """,
        (user_id, provider_type, provider_id)
    )
    return get_auth_by_id(auth_id)


# ─────────────────────────────────────────────
# 2. 로그인 검증
# ─────────────────────────────────────────────

def login_local(email: str, plain_password: str) -> User:
    """
    local 이메일/비밀번호 로그인 검증.
    - 이메일 미존재, 비밀번호 불일치, 계정 비활성 시 예외 발생
    - 성공 시 User 반환 (JWT 발급은 라우터에서 처리)

    사용 예시:
        user = login_local("test@test.com", "plain_password_123")
    """
    # user_service에서 사용자 조회 (단방향 의존)
    user = get_user_by_email(email)
    if not user:
        raise ValueError("존재하지 않는 이메일입니다.")
    if not user.is_active:
        raise ValueError("비활성화된 계정입니다.")

    # local 로그인 수단 조회
    auth_row = execute_one(
        """
        SELECT password_hash FROM auth_providers
        WHERE user_id = %s AND provider_type = 'local'
        """,
        (user.user_id,)
    )
    if not auth_row:
        raise ValueError("local 로그인 수단이 등록되지 않은 계정입니다.")
    if not _verify_password(plain_password, auth_row["password_hash"]):
        raise ValueError("비밀번호가 일치하지 않습니다.")

    return user


def login_social(provider_type: str, provider_id: str) -> User:
    """
    소셜 로그인 검증 (google / kakao).
    - provider_type + provider_id로 연결된 계정 조회
    - 연결된 계정이 없으면 예외 발생 (회원가입 필요)
    - 성공 시 User 반환 (JWT 발급은 라우터에서 처리)

    사용 예시:
        user = login_social("google", "google_uid_abc123")
    """
    auth_row = execute_one(
        """
        SELECT user_id FROM auth_providers
        WHERE provider_type = %s AND provider_id = %s
        """,
        (provider_type, provider_id)
    )
    if not auth_row:
        raise ValueError(f"연결된 {provider_type} 계정이 없습니다. 회원가입이 필요합니다.")

    from services.user_service import get_user_by_id
    user = get_user_by_id(auth_row["user_id"])
    if not user:
        raise ValueError("연결된 사용자를 찾을 수 없습니다.")
    if not user.is_active:
        raise ValueError("비활성화된 계정입니다.")

    return user


# ─────────────────────────────────────────────
# 3. 로그인 수단 조회
# ─────────────────────────────────────────────

def get_auth_by_id(auth_id: int) -> Optional[AuthProvider]:
    """
    auth_id로 로그인 수단 단건 조회.

    사용 예시:
        auth = get_auth_by_id(1)
    """
    row = execute_one(
        "SELECT * FROM auth_providers WHERE auth_id = %s",
        (auth_id,)
    )
    return AuthProvider.from_dict(row) if row else None


def get_auth_by_user(user_id: int) -> list[AuthProvider]:
    """
    user_id로 연결된 전체 로그인 수단 조회.
    - 한 계정에 local + 소셜 복수 연결 가능

    사용 예시:
        auths = get_auth_by_user(1)
        provider_types = [a.provider_type for a in auths]
        # 예: ["local", "google"]
    """
    from db.db_manager import execute_query
    rows = execute_query(
        "SELECT * FROM auth_providers WHERE user_id = %s",
        (user_id,)
    )
    return [AuthProvider.from_dict(row) for row in rows]