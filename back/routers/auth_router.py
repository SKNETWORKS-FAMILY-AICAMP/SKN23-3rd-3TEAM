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

import os
from urllib.parse import urlencode

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from services.auth_service import (
    get_google_login_url,
    google_callback,
    get_kakao_login_url,
    kakao_callback,
    get_naver_login_url,
    naver_callback,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")


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


@router.get("/google/callback")
async def google_callback_handler(code: str):
    """
    Google 인증 완료 후 콜백.
    - Google이 code를 query parameter로 전달
    - code → access_token → 사용자 정보 → JWT 발급
    - 성공: 프론트 /oauth/callback?token=<jwt>로 리디렉션
    - 실패: 프론트 /oauth/callback?error=<message>로 리디렉션
    """
    try:
        result  = await google_callback(code)
        token   = result["access_token"]
        is_new  = result.get("is_new", False)
        return RedirectResponse(f"{FRONTEND_BASE_URL}/oauth/callback?{urlencode({'token': token, 'provider': 'google', 'is_new': str(is_new).lower()})}")
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_BASE_URL}/oauth/callback?{urlencode({'error': str(e)})}")


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


@router.get("/kakao/callback")
async def kakao_callback_handler(code: str):
    """
    Kakao 인증 완료 후 콜백.
    - Kakao가 code를 query parameter로 전달
    - code → access_token → 사용자 정보 → JWT 발급
    - 성공: 프론트 /oauth/callback?token=<jwt>로 리디렉션
    - 실패: 프론트 /oauth/callback?error=<message>로 리디렉션
    """
    try:
        result  = await kakao_callback(code)
        token   = result["access_token"]
        is_new  = result.get("is_new", False)
        return RedirectResponse(f"{FRONTEND_BASE_URL}/oauth/callback?{urlencode({'token': token, 'provider': 'kakao', 'is_new': str(is_new).lower()})}")
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_BASE_URL}/oauth/callback?{urlencode({'error': str(e)})}")


# ─────────────────────────────────────────────
# Naver 소셜 로그인
# ─────────────────────────────────────────────

@router.get("/naver/login")
def naver_login():
    """
    Naver 로그인 페이지로 리디렉션.

    프론트 요청 예시:
        브라우저에서 직접 접속 또는
        GET /auth/naver/login
    """
    url = get_naver_login_url()
    return RedirectResponse(url)


@router.get("/naver/callback")
async def naver_callback_handler(code: str, state: str):
    """
    Naver 인증 완료 후 콜백.
    - Naver가 code와 state를 query parameter로 전달
    - code + state → access_token → 사용자 정보 → JWT 발급
    - 성공: 프론트 /oauth/callback?token=<jwt>로 리디렉션
    - 실패: 프론트 /oauth/callback?error=<message>로 리디렉션
    """
    try:
        result  = await naver_callback(code, state)
        token   = result["access_token"]
        is_new  = result.get("is_new", False)
        return RedirectResponse(f"{FRONTEND_BASE_URL}/oauth/callback?{urlencode({'token': token, 'provider': 'naver', 'is_new': str(is_new).lower()})}")
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_BASE_URL}/oauth/callback?{urlencode({'error': str(e)})}")