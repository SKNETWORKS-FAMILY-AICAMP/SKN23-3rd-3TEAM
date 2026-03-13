import os
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

"""
deps.py
─────────────────────────────────────────────────────────────
역할  : FastAPI Depends() 공통 의존성 모음
        현재: Authorization 헤더에서 user_id 추출
        실제 JWT 도입 후 이 파일만 수정하면 됨
─────────────────────────────────────────────────────────────
"""

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme_in_production")
ALGORITHM  = "HS256"

# Authorization: Bearer <token> 헤더 파싱 자동화
_bearer = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> int:
    """
    JWT access_token에서 user_id(sub) 추출 후 반환.
    토큰이 없거나 유효하지 않으면 401 반환.

    사용 예시 (라우터):
        @router.get("/me")
        def get_me(user_id: int = Depends(get_current_user_id)):
            ...
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int | None = payload.get("sub")

        if user_id is None:
            raise credentials_exception
        
        return int(user_id)
    except (JWTError, ValueError):
        raise credentials_exception

# ─────────────────────────────────────────────
# JWT 발급 헬퍼 (user_router에서 사용)
# ─────────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    """
    user_id를 sub 클레임으로 담은 JWT access_token 생성.

    사용 예시 (user_router.py):
        from .deps import create_access_token
        token = create_access_token(user.user_id)
    """

    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
