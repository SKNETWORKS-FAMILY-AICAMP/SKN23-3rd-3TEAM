"""
main.py
─────────────────────────────────────────────────────────────
FastAPI 앱 진입점.
역할  :
    1. FastAPI 앱 인스턴스 생성
    2. CORS 미들웨어 설정 (프론트 개발 서버 허용)
    3. 라우터 등록 (users / chats / analysis)
    4. 앱 시작 시 DB 초기화 / 종료 시 SSH 터널 정리
─────────────────────────────────────────────────────────────
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from db.db_manager import init_db, close_tunnel
from routers.user_router     import router as user_router
from routers.chat_router     import router as chat_router
from routers.analysis_router import router as analysis_router
from routers.wishlist_router import router as wishlist_router
from routers.upload_router   import router as upload_router
from routers.keyword_router  import router as keyword_router

load_dotenv()


# ─────────────────────────────────────────────
# 앱 생명주기 (시작 / 종료)
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ 앱 시작 시 DB 초기화, 종료 시 SSH 터널 닫기 """
    init_db()
    yield
    close_tunnel()


# ─────────────────────────────────────────────
# FastAPI 앱 생성
# ─────────────────────────────────────────────

app = FastAPI(
    title       = "AI 피부 분석 챗봇 API",
    description = "피부 분석 · 채팅 · 위시리스트 관련 REST API",
    version     = "0.1.0",
    lifespan    = lifespan,
)


# ─────────────────────────────────────────────
# CORS 설정
# ─────────────────────────────────────────────

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000"   # Vite 기본 포트
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ─────────────────────────────────────────────
# 라우터 등록
# ─────────────────────────────────────────────

app.include_router(user_router)      # /users/...
app.include_router(chat_router)      # /chats/...
app.include_router(analysis_router)  # /analysis/...
app.include_router(wishlist_router)  # /wishlist/...
app.include_router(upload_router)    # /upload
app.include_router(keyword_router)   # /keywords


# ─────────────────────────────────────────────
# 헬스체크
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    """
    서버 상태 확인용 엔드포인트.

    응답:
        { "status": "ok" }
    """
    return {"status": "ok"}
