"""
auth_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    GET    /auth/google/login       Google 로그인 URL로 리디렉션
    GET    /auth/google/callback    Google 인증 후 콜백 처리 → JWT 반환
    GET    /auth/kakao/login        Kakao 로그인 URL로 리디렉션
    GET    /auth/kakao/callback     Kakao 인증 후 콜백 처리 → JWT 반환
─────────────────────────────────────────────────────────────
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from services.auth_service import (
    get_google_login_url,
    google_callback,
    get_kakao_login_url,
    kakao_callback,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ─────────────────────────────────────────────
# 응답 모델
# ─────────────────────────────────────────────

class SocialLoginResponse(BaseModel):
    access_token : str
    token_type   : str = "bearer"


# ─────────────────────────────────────────────
# Google 소셜 로그인
# ─────────────────────────────────────────────

@router.get("/google/login")
def google_login():
    """
    Google 로그인 페이지로 리디렉션.

    프론트 요청 예시:
        브라우저에서 직접 접속 또는
        GET /auth/google/login
    """
    url = get_google_login_url()
    return RedirectResponse(url)


@router.get("/google/callback", response_model=SocialLoginResponse)
async def google_callback_handler(code: str):
    """
    Google 인증 완료 후 콜백.
    - Google이 code를 query parameter로 전달
    - code → access_token → 사용자 정보 → JWT 발급

    응답:
        { "access_token": "eyJ...", "token_type": "bearer" }
    """
    try:
        result = await google_callback(code)
        return SocialLoginResponse(access_token=result["access_token"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google 로그인 처리 중 오류: {str(e)}")


# ─────────────────────────────────────────────
# Kakao 소셜 로그인
# ─────────────────────────────────────────────

@router.get("/kakao/login")
def kakao_login():
    """
    Kakao 로그인 페이지로 리디렉션.

    프론트 요청 예시:
        브라우저에서 직접 접속 또는
        GET /auth/kakao/login
    """
    url = get_kakao_login_url()
    return RedirectResponse(url)


@router.get("/kakao/callback", response_model=SocialLoginResponse)
async def kakao_callback_handler(code: str):
    """
    Kakao 인증 완료 후 콜백.
    - Kakao가 code를 query parameter로 전달
    - code → access_token → 사용자 정보 → JWT 발급

    응답:
        { "access_token": "eyJ...", "token_type": "bearer" }
    """
    try:
        result = await kakao_callback(code)
        return SocialLoginResponse(access_token=result["access_token"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kakao 로그인 처리 중 오류: {str(e)}")