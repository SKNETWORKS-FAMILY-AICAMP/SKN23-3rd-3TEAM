"""
auth_service.py
─────────────────────────────────────────────────────────────
목적  : 인증 및 로그인 관련 비즈니스 로직 담당
역할  :
    1. local 로그인 수단 등록 (비밀번호 해시 포함)
    2. local 이메일/비밀번호 로그인 검증
    3. Google / Kakao 소셜 로그인 처리
    4. 로그인 수단 조회

흐름:
    FastAPI 라우터 → auth_service 함수 호출
                    → db_manager 헬퍼로 DB 접근
                    → models.AuthProvider / User 로 변환 후 반환

의존성:
    auth_service → user_service (단방향)
    JWT 발급은 routers/deps.py의 create_access_token() 사용
─────────────────────────────────────────────────────────────
"""

import os
import bcrypt
import httpx
from typing import Optional

from dotenv import load_dotenv

from db.db_manager import execute_one, execute_write, execute_query
from db.models import AuthProvider, User
from db.schemas import AuthProviderCreate, UserCreate
from services.user_service import (
    get_user_by_email,
    get_user_by_id,
    create_user,
)
# JWT 발급은 deps.py에서 통합 관리
from routers.deps import create_access_token

load_dotenv()

# ─────────────────────────────────────────────
# 환경변수 로드
# ─────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI")

KAKAO_CLIENT_ID      = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET  = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI   = os.getenv("KAKAO_REDIRECT_URI")

NAVER_CLIENT_ID      = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET  = os.getenv("NAVER_CLIENT_SECRET")
NAVER_REDIRECT_URI   = os.getenv("NAVER_REDIRECT_URI")


# ─────────────────────────────────────────────
# 1. 비밀번호 헬퍼
# ─────────────────────────────────────────────

def _hash_password(plain_password: str) -> str:
    """ 평문 비밀번호 → bcrypt 해시 변환 """
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain_password: str, hashed: str) -> bool:
    """ 평문 비밀번호와 해시 일치 여부 확인 """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))


# ─────────────────────────────────────────────
# 2. local 로그인 수단 등록 / 검증
# ─────────────────────────────────────────────

def register_local_auth(user_id: int, email: str, plain_password: str) -> AuthProvider:
    """
    local 로그인 수단 등록.
    - 비밀번호를 bcrypt로 해시 후 auth_providers에 INSERT
    - create_user() 호출 직후 함께 사용

    사용 예시:
        user = create_user(data)
        auth = register_local_auth(user.user_id, user.email, "plain_password_123")
    """
    existing = execute_one(
        "SELECT auth_id FROM auth_providers WHERE user_id = %s AND provider_type = 'local'",
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


def login_local(email: str, plain_password: str) -> dict:
    """
    local 이메일/비밀번호 로그인 검증.
    - 성공 시 JWT 토큰과 User 반환
    - JWT 발급은 deps.py의 create_access_token() 사용

    사용 예시:
        result = login_local("test@test.com", "plain_password_123")
        token  = result["access_token"]
        user   = result["user"]
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

    # deps.py의 create_access_token 사용 (user_id만 전달)
    token = create_access_token(user.user_id)
    return {"access_token": token, "token_type": "bearer", "user": user}


# ─────────────────────────────────────────────
# 3. Google 소셜 로그인
# ─────────────────────────────────────────────

def get_google_login_url() -> str:
    """
    Google OAuth 인증 URL 생성.
    - 프론트에서 이 URL로 리디렉션하면 Google 로그인 화면으로 이동

    사용 예시:
        url = get_google_login_url()
        return RedirectResponse(url)
    """
    return (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid email profile"
    )


async def google_callback(code: str) -> dict:
    """
    Google 인증 콜백 처리.
    1. code → access_token 교환
    2. access_token → Google 사용자 정보 조회
    3. 신규 유저면 자동 회원가입 + 소셜 로그인 수단 등록
       기존 유저면 로그인 처리
    4. JWT 발급 후 반환

    사용 예시:
        result = await google_callback(code)
        token  = result["access_token"]
        user   = result["user"]
    """
    async with httpx.AsyncClient() as client:

        # 1. code → access_token 교환
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code"          : code,
                "client_id"     : GOOGLE_CLIENT_ID,
                "client_secret" : GOOGLE_CLIENT_SECRET,
                "redirect_uri"  : GOOGLE_REDIRECT_URI,
                "grant_type"    : "authorization_code",
            }
        )
        token_data   = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"Google access_token 발급 실패: {token_data}")

        # 2. access_token → Google 사용자 정보 조회
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info   = user_res.json()
        provider_id = user_info.get("id")       # Google 고유 사용자 ID
        email       = user_info.get("email")
        name        = user_info.get("name", "")

        if not provider_id or not email:
            raise ValueError("Google 사용자 정보 조회 실패")

    # 3. 신규/기존 유저 처리
    user, is_new = _get_or_create_social_user(
        provider_type = "google",
        provider_id   = provider_id,
        email         = email,
        name          = name,
    )

    # 4. JWT 발급 (deps.py 사용)
    token = create_access_token(user.user_id)
    return {"access_token": token, "token_type": "bearer", "user": user, "is_new": is_new}


# ─────────────────────────────────────────────
# 4. Kakao 소셜 로그인
# ─────────────────────────────────────────────

def get_kakao_login_url() -> str:
    """
    Kakao OAuth 인증 URL 생성.
    - 프론트에서 이 URL로 리디렉션하면 카카오 로그인 화면으로 이동

    사용 예시:
        url = get_kakao_login_url()
        return RedirectResponse(url)
    """
    return (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        "&response_type=code"
    )


async def kakao_callback(code: str) -> dict:
    """
    Kakao 인증 콜백 처리.
    1. code → access_token 교환
    2. access_token → Kakao 사용자 정보 조회
    3. 신규 유저면 자동 회원가입 + 소셜 로그인 수단 등록
       기존 유저면 로그인 처리
    4. JWT 발급 후 반환

    사용 예시:
        result = await kakao_callback(code)
        token  = result["access_token"]
        user   = result["user"]
    """
    async with httpx.AsyncClient() as client:

        # 1. code → access_token 교환
        token_res = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "code"          : code,
                "client_id"     : KAKAO_CLIENT_ID,
                "client_secret" : KAKAO_CLIENT_SECRET,
                "redirect_uri"  : KAKAO_REDIRECT_URI,
                "grant_type"    : "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token_data   = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"Kakao access_token 발급 실패: {token_data}")

        # 2. access_token → Kakao 사용자 정보 조회
        user_res = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info     = user_res.json()
        provider_id   = str(user_info.get("id"))  # Kakao 고유 사용자 ID
        kakao_account = user_info.get("kakao_account", {})
        email         = kakao_account.get("email")
        name          = kakao_account.get("profile", {}).get("nickname", "")

        if not provider_id or not email:
            raise ValueError("Kakao 사용자 정보 조회 실패 (이메일 동의 필요)")

    # 3. 신규/기존 유저 처리
    user, is_new = _get_or_create_social_user(
        provider_type = "kakao",
        provider_id   = provider_id,
        email         = email,
        name          = name,
    )

    # 4. JWT 발급 (deps.py 사용)
    token = create_access_token(user.user_id)
    return {"access_token": token, "token_type": "bearer", "user": user, "is_new": is_new}


# ─────────────────────────────────────────────
# 5. Naver 소셜 로그인
# ─────────────────────────────────────────────

def get_naver_login_url() -> str:
    """
    Naver OAuth 인증 URL 생성.
    - state 파라미터는 CSRF 방지용 임의 문자열 (Naver 필수 요구)
    - 프론트에서 이 URL로 리디렉션하면 네이버 로그인 화면으로 이동

    사용 예시:
        url = get_naver_login_url()
        return RedirectResponse(url)
    """
    import secrets
    state = secrets.token_urlsafe(16)
    return (
        "https://nid.naver.com/oauth2.0/authorize"
        f"?client_id={NAVER_CLIENT_ID}"
        f"&redirect_uri={NAVER_REDIRECT_URI}"
        "&response_type=code"
        f"&state={state}"
    )


async def naver_callback(code: str, state: str) -> dict:
    """
    Naver 인증 콜백 처리.
    1. code + state → access_token 교환
    2. access_token → Naver 사용자 정보 조회
    3. 신규 유저면 자동 회원가입 + 소셜 로그인 수단 등록
       기존 유저면 로그인 처리
    4. JWT 발급 후 반환

    사용 예시:
        result = await naver_callback(code, state)
        token  = result["access_token"]
        user   = result["user"]
    """
    async with httpx.AsyncClient() as client:

        # 1. code → access_token 교환
        token_res = await client.get(
            "https://nid.naver.com/oauth2.0/token",
            params={
                "grant_type"    : "authorization_code",
                "client_id"     : NAVER_CLIENT_ID,
                "client_secret" : NAVER_CLIENT_SECRET,
                "redirect_uri"  : NAVER_REDIRECT_URI,
                "code"          : code,
                "state"         : state,
            }
        )
        token_data   = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"Naver access_token 발급 실패: {token_data}")

        # 2. access_token → Naver 사용자 정보 조회
        user_res = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info   = user_res.json()
        response    = user_info.get("response", {})
        provider_id = str(response.get("id", ""))
        email       = response.get("email")
        name        = response.get("name", "")

        if not provider_id or not email:
            raise ValueError("Naver 사용자 정보 조회 실패 (이메일 동의 필요)")

    # 3. 신규/기존 유저 처리
    user, is_new = _get_or_create_social_user(
        provider_type = "naver",
        provider_id   = provider_id,
        email         = email,
        name          = name,
    )

    # 4. JWT 발급 (deps.py 사용)
    token = create_access_token(user.user_id)
    return {"access_token": token, "token_type": "bearer", "user": user, "is_new": is_new}


# ─────────────────────────────────────────────
# 6. 소셜 로그인 공통 헬퍼
# ─────────────────────────────────────────────

def _get_or_create_social_user(
    provider_type : str,
    provider_id   : str,
    email         : str,
    name          : str,
) -> tuple[User, bool]:
    """
    소셜 로그인 공통 처리.
    - 이미 해당 소셜 계정으로 가입된 유저 → (user, False) 반환
    - 같은 이메일로 가입된 유저 → 소셜 수단 추가 연결 후 (user, False) 반환
    - 완전 신규 유저 → 자동 회원가입 + 소셜 수단 등록 후 (user, True) 반환
    """
    # 이미 해당 소셜 계정으로 가입된 유저 확인
    auth_row = execute_one(
        """
        SELECT user_id FROM auth_providers
        WHERE provider_type = %s AND provider_id = %s
        """,
        (provider_type, provider_id)
    )
    if auth_row:
        return get_user_by_id(auth_row["user_id"]), False

    # 같은 이메일로 가입된 유저 확인 → 소셜 수단만 추가 연결
    existing_user = get_user_by_email(email)
    if existing_user:
        execute_write(
            """
            INSERT INTO auth_providers (user_id, provider_type, provider_id)
            VALUES (%s, %s, %s)
            """,
            (existing_user.user_id, provider_type, provider_id)
        )
        return existing_user, False

    # 완전 신규 유저 → 자동 회원가입
    # 닉네임 중복 방지를 위해 provider_id 뒤 6자리 붙임
    nickname = f"{name}_{provider_id[-6:]}" if name else f"user_{provider_id[-6:]}"
    user = create_user(UserCreate(
        email          = email,
        name           = name or "소셜유저",
        nickname       = nickname,
        terms_agreed   = True,
        privacy_agreed = True,
    ))
    execute_write(
        """
        INSERT INTO auth_providers (user_id, provider_type, provider_id)
        VALUES (%s, %s, %s)
        """,
        (user.user_id, provider_type, provider_id)
    )
    return user, True


# ─────────────────────────────────────────────
# 6. 로그인 수단 조회
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
        auths     = get_auth_by_user(1)
        providers = [a.provider_type for a in auths]
        # 예: ["local", "google"]
    """
    rows = execute_query(
        "SELECT * FROM auth_providers WHERE user_id = %s",
        (user_id,)
    )
    return [AuthProvider.from_dict(row) for row in rows]

def get_linked_social_providers(user_id: int) -> list[str]:
    """
    user_id에 연결된 소셜 provider_type 목록 반환 (local 제외)
    예: ["kakao", "google"]
    """
    rows = execute_query(
        """
        SELECT DISTINCT provider_type
        FROM auth_providers
        WHERE user_id = %s AND provider_type != 'local'
        ORDER BY provider_type
        """,
        (user_id,)
    )
    return [r["provider_type"] for r in rows]