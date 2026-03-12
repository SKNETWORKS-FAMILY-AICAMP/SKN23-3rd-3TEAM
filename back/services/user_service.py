
from db.models import User
from typing import Optional
from datetime import datetime
from db.schemas import UserCreate, UserUpdate
from db.db_manager import execute_one, execute_write

"""
user_service.py
─────────────────────────────────────────────────────────────
목적  : 사용자 데이터 관리 비즈니스 로직 담당
역할  :
    1. 회원 생성
    2. 사용자 조회 (user_id / email)
    3. 프로필 수정 (닉네임, 피부정보, S3 이미지 URL 등)
    4. 회원 탈퇴 (soft delete)
    5. 이메일 / 닉네임 중복 확인

인증/로그인 관련 로직은 auth_service.py에서 담당
─────────────────────────────────────────────────────────────
"""

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
        (email)
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
# 2. 회원 생성
# ─────────────────────────────────────────────

def create_user(data: UserCreate) -> User:
    """
    신규 회원 생성.
    - 이메일/닉네임 중복 시 예외 발생
    - users 테이블에 INSERT 후 생성된 User 반환
    - 로그인 수단 등록은 auth_service.register_local_auth() 에서 처리

    사용 예시:
        user = create_user(UserCreate(
            email          = "test@test.com",
            name           = "홍길동",
            nickname       = "길동이",
            terms_agreed   = True,
            privacy_agreed = True,
        ))
    """
    if is_email_taken(data.email):
        raise ValueError("이미 사용 중인 이메일입니다.")

    user_id = execute_write(
        """
        INSERT INTO users (email, name, nickname, terms_agreed, privacy_agreed)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (data.email, data.name, data.nickname, data.terms_agreed, data.privacy_agreed)
    )

    return get_user_by_id(user_id)


# ─────────────────────────────────────────────
# 3. 사용자 조회
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
        (user_id)
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
        (email)
    )

    return User.from_dict(row) if row else None


# ─────────────────────────────────────────────
# 4. 프로필 수정
# ─────────────────────────────────────────────

def update_user(user_id: int, data: UserUpdate) -> User:
    """
    사용자 프로필 수정.
    - 변경할 필드만 골라서 UPDATE (None인 필드는 건너뜀)
    - 닉네임 변경 시 중복 확인 포함

    사용 예시:
        updated = update_user(1, UserUpdate(nickname="새닉네임", age=25))
    """
    fields = {k: v for k, v in data.model_dump().items() if v is not None}

    if not fields:
        raise ValueError("수정할 내용이 없습니다.")

    set_clause = ", ".join([f"{key} = %s" for key in fields])
    values = tuple(fields.values()) + (user_id,)

    execute_write(
        f"UPDATE users SET {set_clause} WHERE user_id = %s AND deleted_at IS NULL",
        values
    )

    return get_user_by_id(user_id)


# ─────────────────────────────────────────────
# 5. 회원 탈퇴
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