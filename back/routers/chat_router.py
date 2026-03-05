"""
chat_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    POST   /chats                           채팅방 생성
    GET    /chats                           내 채팅방 목록 조회
    GET    /chats/{chat_room_id}            채팅방 단건 조회
    DELETE /chats/{chat_room_id}            채팅방 삭제 (soft delete)
    POST   /chats/guest/message             비로그인 텍스트 채팅 (DB 저장 없음)
    POST   /chats/{chat_room_id}/messages   메시지 전송 (AI 응답 포함)
    GET    /chats/{chat_room_id}/messages   채팅 히스토리 조회
─────────────────────────────────────────────────────────────
"""

import sys
import os

# 프로젝트 루트를 sys.path에 추가 (ai/ 패키지 import용)
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel

from db.schemas import (
    ChatRoomCreate, ChatRoomResponse,
    MessageCreate, MessageResponse,
)
from services import chat_service
from .deps import get_current_user_id

router = APIRouter(prefix="/chats", tags=["Chat"])


# ─────────────────────────────────────────────
# AI 파이프라인 (지연 import - 서버 시작 속도 보호)
# ─────────────────────────────────────────────

def _run_ai(
    user_text: str,
    image_urls: list[str],
    model_type: str,
    user_id: int,
    chat_history: list[dict],
    is_first_message: bool,
) -> str:
    """
    LangGraph 파이프라인 호출.

    이미지 전달:
      - 프론트가 S3에 업로드한 URL을 받아서 bytes로 다운로드 후 전달
      - vision_node는 bytes 리스트를 받음 (fast: 1장, detailed: 3장)

    analysis_type 매핑:
      프론트 model_type → LangGraph analysis_type
        "simple"     → "quick"
        "detailed"   → "detailed"
        "ingredient" → "ingredient"
        기타          → None (일반 채팅)
    """
    import requests as _requests
    from ai.orchestrator.graph import run

    # model_type → analysis_type 변환
    _type_map = {
        "simple":     "quick",
        "detailed":   "detailed",
        "ingredient": "ingredient",
    }
    analysis_type = _type_map.get(model_type)

    # S3 URL → bytes 변환 (이미지가 있는 경우)
    image_bytes: list[bytes] = []
    if image_urls and analysis_type in ("quick", "detailed", "ingredient"):
        for url in image_urls:
            try:
                resp = _requests.get(url, timeout=10)
                resp.raise_for_status()
                image_bytes.append(resp.content)
            except Exception as e:
                print(f"[chat_router] 이미지 다운로드 실패: {url} → {repr(e)}", flush=True)

    report = run(
        user_text=user_text,
        images=image_bytes,
        analysis_type=analysis_type,
        user_id=user_id,
        chat_history=chat_history,
        is_first_message=is_first_message,
        image_urls=image_urls,          # S3 URL → DB 저장용
    )

    # chat_answer 추출
    return report.get("chat_answer") or "답변을 생성하지 못했어요. 다시 시도해주세요."


def _run_ai_guest(user_text: str, chat_history: list | None = None) -> str:
    """
    비로그인 게스트 AI 응답 (이미지·DB 저장 없음).
    chat_history: 프론트에서 전달한 이전 대화 내역 (임시 프로필 추출용)
    """
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)

    from ai.orchestrator.graph import run

    history = chat_history or []
    report = run(
        user_text=user_text,
        images=[],
        analysis_type=None,
        user_id=None,
        chat_history=history,
        is_first_message=len(history) == 0,
    )
    return report.get("chat_answer") or "답변을 생성하지 못했어요. 다시 시도해주세요."


# ─────────────────────────────────────────────
# 채팅방
# ─────────────────────────────────────────────

@router.post("", response_model=ChatRoomResponse, status_code=201)
def create_chat_room(user_id: int = Depends(get_current_user_id)):
    """
    새 채팅방 생성.
    제목은 첫 메시지 전송 후 자동 설정됨.
    """
    data = ChatRoomCreate(user_id=user_id)
    room = chat_service.create_chat_room(data)
    return _room_to_response(room)


@router.get("", response_model=list[ChatRoomResponse])
def get_my_chat_rooms(user_id: int = Depends(get_current_user_id)):
    """내 채팅방 목록 조회 (최신순)."""
    rooms = chat_service.get_chat_rooms_by_user(user_id)
    return [_room_to_response(r) for r in rooms]


@router.get("/{chat_room_id}", response_model=ChatRoomResponse)
def get_chat_room(chat_room_id: int, user_id: int = Depends(get_current_user_id)):
    """채팅방 단건 조회."""
    room = chat_service.get_chat_room_by_id(chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    if room.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return _room_to_response(room)


@router.delete("/{chat_room_id}", status_code=204)
def delete_chat_room(chat_room_id: int, user_id: int = Depends(get_current_user_id)):
    """채팅방 삭제 (soft delete)."""
    room = chat_service.get_chat_room_by_id(chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    if room.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    chat_service.delete_chat_room(chat_room_id)


# ─────────────────────────────────────────────
# 비로그인 게스트 채팅 (DB 저장 없음)
# ─────────────────────────────────────────────

class GuestMessageRequest(BaseModel):
    content: str
    chat_history: list[dict] | None = None  # 프론트에서 세션 내 대화 내역 전달

class GuestMessageResponse(BaseModel):
    role   : str
    content: str

@router.post("/guest/message", response_model=GuestMessageResponse)
def guest_message(body: GuestMessageRequest):
    """
    비로그인 사용자 텍스트 채팅.
    인증 불필요, DB 저장 없음. 텍스트 입력만 허용.
    실제 LangGraph AI 파이프라인 호출.
    """
    try:
        ai_text = _run_ai_guest(body.content, chat_history=body.chat_history)
    except Exception as e:
        print(f"[guest_message ERROR] {repr(e)}", flush=True)
        ai_text = "잠시 후 다시 시도해주세요."
    return GuestMessageResponse(role="assistant", content=ai_text)


# ─────────────────────────────────────────────
# 메시지
# ─────────────────────────────────────────────

@router.post("/{chat_room_id}/messages", response_model=list[MessageResponse], status_code=201)
def send_message(
    chat_room_id : int,
    body         : MessageCreate,
    user_id      : int = Depends(get_current_user_id),
):
    """
    메시지 전송 후 AI 응답까지 반환.

    흐름:
      1. 채팅방 소유권 확인
      2. 사용자 메시지 DB 저장
      3. 채팅 히스토리 조회 (LLM 컨텍스트용, 최근 20개)
      4. LangGraph AI 파이프라인 실행
         - S3 URL → bytes 변환 → vision_node 전달
         - analysis_type 결정 (model_type 기반)
      5. AI 응답 메시지 DB 저장
      6. [사용자 메시지, AI 응답] 반환

    프론트 요청 예시 (텍스트):
        POST /chats/1/messages
        { "chat_room_id": 1, "role": "user", "model_type": "simple",
          "content": "건성 피부에 맞는 수분크림 추천해줘" }

    프론트 요청 예시 (이미지 + 분석):
        POST /chats/1/messages
        { "chat_room_id": 1, "role": "user", "model_type": "detailed",
          "image_url": ["https://s3.../img1.jpg", "https://s3.../img2.jpg", "https://s3.../img3.jpg"] }
    """
    # 1. 채팅방 소유권 확인
    room = chat_service.get_chat_room_by_id(chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    if room.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 2. 사용자 메시지 DB 저장
    try:
        user_msg = chat_service.save_message(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 첫 메시지이면 채팅방 제목 자동 설정
    is_first = not room.title
    if is_first and body.content:
        title = body.content[:30] + ("..." if len(body.content) > 30 else "")
        chat_service.update_chat_room_title(chat_room_id, title)

    # 3. 채팅 히스토리 조회 (방금 저장한 사용자 메시지 제외, 직전 대화만)
    history_msgs = chat_service.get_messages_by_room(chat_room_id)
    # 방금 저장한 메시지 제외하고 LLM에 전달
    chat_history = [
        {"role": m.role, "content": m.content or ""}
        for m in history_msgs[:-1]  # 마지막(방금 저장한 것) 제외
        if m.role in ("user", "assistant") and m.content
    ]

    # 4. LangGraph AI 파이프라인 실행
    image_urls = body.image_url or []
    user_text  = body.content or ""

    try:
        ai_text = _run_ai(
            user_text=user_text,
            image_urls=image_urls,
            model_type=body.model_type,
            user_id=user_id,
            chat_history=chat_history,
            is_first_message=is_first,
        )
    except Exception as e:
        print(f"[send_message AI ERROR] {repr(e)}", flush=True)
        ai_text = "잠시 후 다시 시도해주세요."

    # 5. AI 응답 메시지 DB 저장
    ai_msg_data = MessageCreate(
        chat_room_id = chat_room_id,
        role         = "assistant",
        model_type   = body.model_type,
        content      = ai_text,
    )
    ai_msg = chat_service.save_message(ai_msg_data)

    return [_msg_to_response(user_msg), _msg_to_response(ai_msg)]


@router.get("/{chat_room_id}/messages", response_model=list[MessageResponse])
def get_messages(
    chat_room_id : int,
    role         : Optional[str] = None,
    user_id      : int = Depends(get_current_user_id),
):
    """
    채팅방 메시지 히스토리 조회 (시간 오름차순).
    role 쿼리 파라미터로 특정 역할의 메시지만 필터링 가능.
    """
    room = chat_service.get_chat_room_by_id(chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    if room.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    if role:
        messages = chat_service.get_messages_by_role(chat_room_id, role)
    else:
        messages = chat_service.get_messages_by_room(chat_room_id)

    return [_msg_to_response(m) for m in messages]


# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────

def _room_to_response(room) -> ChatRoomResponse:
    return ChatRoomResponse(
        chat_room_id = room.chat_room_id,
        user_id      = room.user_id,
        title        = room.title,
        created_at   = room.created_at,
    )


def _msg_to_response(msg) -> MessageResponse:
    return MessageResponse(
        message_id   = msg.message_id,
        chat_room_id = msg.chat_room_id,
        role         = msg.role,
        model_type   = msg.model_type,
        content      = msg.content,
        image_url    = msg.image_url,
        created_at   = msg.created_at,
    )
