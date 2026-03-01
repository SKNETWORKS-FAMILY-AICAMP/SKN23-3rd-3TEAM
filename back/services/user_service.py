"""
user_service.py
─────────────────────────────────────────────────────────────
목적  : 사용자 관련 비즈니스 로직 담당
역할  :
    1. 회원가입 (local / 소셜)
    2. 로그인 (local 비밀번호 검증)
    3. 사용자 조회 (user_id / email)
    4. 프로필 수정 (닉네임, 피부정보, S3 이미지 URL 등)
    5. 회원 탈퇴 (soft delete)
    6. 닉네임 / 이메일 중복 확인

흐름:
    FastAPI 라우터 → user_service 함수 호출
                    → db_manager 헬퍼로 DB 접근
                    → models.User 로 변환 후 반환
─────────────────────────────────────────────────────────────
"""

import bcrypt
from datetime import datetime
from typing import Optional

from db.db_manager import execute_one, execute_write, execute_query
from db.models import User, AuthProvider
from db.schemas import UserCreate, UserUpdate, AuthProviderCreate


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
# 1. 중복 확인
# ─────────────────────────────────────────────

def is_email_taken(email: str) -> bool:
    """
    이메일 중복 확인.
    이미 존재하면 True 반환.

    사용 예시:
        if is_email_taken("test@test.com"):
            raise HTTPException(400, "이미 사용 중인 이메일입니다.")
    """
    row = execute_one(
        "SELECT user_id FROM users WHERE email = %s AND deleted_at IS NULL",
        (email,)
    )
    return row is not None


def is_nickname_taken(nickname: str) -> bool:
    """
    닉네임 중복 확인.
    이미 존재하면 True 반환.

    사용 예시:
        if is_nickname_taken("홍길동"):
            raise HTTPException(400, "이미 사용 중인 닉네임입니다.")
    """
    row = execute_one(
        "SELECT user_id FROM users WHERE nickname = %s AND deleted_at IS NULL",
        (nickname,)
    )
    return row is not None


# ─────────────────────────────────────────────
# 2. 회원가입
# ─────────────────────────────────────────────

def create_user(data: UserCreate) -> User:
    """
    신규 회원 생성.
    - 이메일/닉네임 중복 시 예외 발생
    - users 테이블에 INSERT 후 생성된 User 반환

    사용 예시:
        user = create_user(UserCreate(
            email="test@test.com",
            name="홍길동",
            nickname="길동이",
            terms_agreed=True,
            privacy_agreed=True
        ))
    """
    if is_email_taken(data.email):
        raise ValueError("이미 사용 중인 이메일입니다.")
    if is_nickname_taken(data.nickname):
        raise ValueError("이미 사용 중인 닉네임입니다.")

    user_id = execute_write(
        """
        INSERT INTO users (email, name, nickname, terms_agreed, privacy_agreed)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (data.email, data.name, data.nickname, data.terms_agreed, data.privacy_agreed)
    )
    return get_user_by_id(user_id)


def register_local_auth(user_id: int, email: str, plain_password: str) -> AuthProvider:
    """
    local 로그인 수단 등록.
    - 비밀번호를 bcrypt로 해시 후 auth_providers에 INSERT
    - create_user() 호출 직후 함께 사용

    사용 예시:
        user = create_user(data)
        auth = register_local_auth(user.user_id, user.email, "plain_password_123")
    """
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
    row = execute_one(
        "SELECT * FROM auth_providers WHERE auth_id = %s",
        (auth_id,)
    )
    return AuthProvider.from_dict(row)


def register_social_auth(user_id: int, provider_type: str, provider_id: str) -> AuthProvider:
    """
    소셜 로그인 수단 등록 (google / kakao).
    - 이미 연결된 소셜 계정이면 예외 발생

    사용 예시:
        auth = register_social_auth(user.user_id, "google", "google_uid_abc123")
    """
    existing = execute_one(
        "SELECT auth_id FROM auth_providers WHERE provider_type = %s AND provider_id = %s",
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
    row = execute_one(
        "SELECT * FROM auth_providers WHERE auth_id = %s",
        (auth_id,)
    )
    return AuthProvider.from_dict(row)


# ─────────────────────────────────────────────
# 3. 로그인
# ─────────────────────────────────────────────

def login_local(email: str, plain_password: str) -> User:
    """
    local 이메일/비밀번호 로그인.
    - 이메일 미존재, 비밀번호 불일치, 계정 비활성 시 예외 발생
    - 성공 시 User 반환 (JWT 발급은 라우터에서 처리)

    사용 예시:
        user = login_local("test@test.com", "plain_password_123")
    """
    user = get_user_by_email(email)
    if not user:
        raise ValueError("존재하지 않는 이메일입니다.")
    if not user.is_active:
        raise ValueError("비활성화된 계정입니다.")

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


# ─────────────────────────────────────────────
# 4. 사용자 조회
# ─────────────────────────────────────────────

def get_user_by_id(user_id: int) -> Optional[User]:
    """
    user_id로 사용자 조회.
    탈퇴한 사용자는 반환하지 않음 (soft delete 고려).

    사용 예시:
        user = get_user_by_id(1)
    """
    row = execute_one(
        "SELECT * FROM users WHERE user_id = %s AND deleted_at IS NULL",
        (user_id,)
    )
    return User.from_dict(row) if row else None


def get_user_by_email(email: str) -> Optional[User]:
    """
    이메일로 사용자 조회.
    탈퇴한 사용자는 반환하지 않음.

    사용 예시:
        user = get_user_by_email("test@test.com")
    """
    row = execute_one(
        "SELECT * FROM users WHERE email = %s AND deleted_at IS NULL",
        (email,)
    )
    return User.from_dict(row) if row else None


# ─────────────────────────────────────────────
# 5. 프로필 수정
# ─────────────────────────────────────────────

def update_user(user_id: int, data: UserUpdate) -> User:
    """
    사용자 프로필 수정.
    - 변경할 필드만 골라서 UPDATE (None인 필드는 건너뜀)
    - 닉네임 변경 시 중복 확인 포함

    사용 예시:
        updated = update_user(1, UserUpdate(nickname="새닉네임", age=25))
    """
    # 수정할 필드만 추출 (None 제외)
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not fields:
        raise ValueError("수정할 내용이 없습니다.")

    # 닉네임 변경 시 중복 확인
    if "nickname" in fields and is_nickname_taken(fields["nickname"]):
        raise ValueError("이미 사용 중인 닉네임입니다.")

    # 동적 UPDATE 쿼리 생성
    set_clause = ", ".join([f"{key} = %s" for key in fields])
    values = tuple(fields.values()) + (user_id,)

    execute_write(
        f"UPDATE users SET {set_clause} WHERE user_id = %s AND deleted_at IS NULL",
        values
    )
    return get_user_by_id(user_id)


# ─────────────────────────────────────────────
# 6. 회원 탈퇴
# ─────────────────────────────────────────────

def delete_user(user_id: int) -> bool:
    """
    회원 탈퇴 처리 (soft delete).
    - deleted_at에 현재 시각 기록, is_active = FALSE 처리
    - 실제 데이터는 삭제하지 않음 (복구 가능)

    사용 예시:
        success = delete_user(1)
    """
    affected = execute_write(
        """
        UPDATE users
        SET deleted_at = %s, is_active = FALSE
        WHERE user_id = %s AND deleted_at IS NULL
        """,
        (datetime.now(), user_id)
    )
    return affected > 0


# ─────────────────────────────────────────────
# 7. 비밀번호 재설정
# ─────────────────────────────────────────────

def reset_password(email: str, new_password: str) -> bool:
    """
    비밀번호 재설정.
    - auth_providers의 password_hash를 새 비밀번호 해시로 업데이트
    - OTP 검증은 라우터에서 처리 후 호출

    사용 예시:
        reset_password("user@example.com", "new_password_123!")
    """
    user = get_user_by_email(email)
    if not user:
        raise ValueError("존재하지 않는 이메일입니다.")

    hashed = _hash_password(new_password)
    affected = execute_write(
        """
        UPDATE auth_providers
        SET password_hash = %s
        WHERE user_id = %s AND provider_type = 'local'
        """,
        (hashed, user.user_id)
    )
    if affected == 0:
        raise ValueError("local 로그인 수단이 등록되지 않은 계정입니다.")
    return True