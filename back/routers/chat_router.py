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
# 채팅방
# ─────────────────────────────────────────────

@router.post("", response_model=ChatRoomResponse, status_code=201)
def create_chat_room(user_id: int = Depends(get_current_user_id)):
    """
    새 채팅방 생성.
    제목은 첫 메시지 전송 후 자동 설정됨.

    프론트 요청 예시:
        POST /chats
        Headers: { Authorization: "Bearer <token>" }
    응답:
        { "chat_room_id": 1, "user_id": 1, "title": null, "created_at": "..." }
    """
    data = ChatRoomCreate(user_id=user_id)
    room = chat_service.create_chat_room(data)
    return _room_to_response(room)


@router.get("", response_model=list[ChatRoomResponse])
def get_my_chat_rooms(user_id: int = Depends(get_current_user_id)):
    """
    내 채팅방 목록 조회 (최신순).

    프론트 요청 예시:
        GET /chats
    응답:
        [ { "chat_room_id": 2, "title": "건성 피부 보습 상담", ... }, ... ]
    """
    rooms = chat_service.get_chat_rooms_by_user(user_id)
    return [_room_to_response(r) for r in rooms]


@router.get("/{chat_room_id}", response_model=ChatRoomResponse)
def get_chat_room(chat_room_id: int, user_id: int = Depends(get_current_user_id)):
    """
    채팅방 단건 조회.

    프론트 요청 예시:
        GET /chats/1
    """
    room = chat_service.get_chat_room_by_id(chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    if room.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return _room_to_response(room)


@router.delete("/{chat_room_id}", status_code=204)
def delete_chat_room(chat_room_id: int, user_id: int = Depends(get_current_user_id)):
    """
    채팅방 삭제 (soft delete).

    프론트 요청 예시:
        DELETE /chats/1
    """
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

class GuestMessageResponse(BaseModel):
    role   : str
    content: str

@router.post("/guest/message", response_model=GuestMessageResponse)
def guest_message(body: GuestMessageRequest):
    """
    비로그인 사용자 텍스트 채팅.
    인증 불필요, DB 저장 없음. 텍스트 입력만 허용.

    프론트 요청 예시:
        POST /chats/guest/message
        { "content": "건성 피부에 맞는 수분크림 추천해줘" }
    응답:
        { "role": "assistant", "content": "세라마이드가 풍부한..." }
    """
    ai_response_text = "[AI 응답 예시] 건성 피부에는 세라마이드 함유 보습크림을 추천드립니다."
    return GuestMessageResponse(role="assistant", content=ai_response_text)


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
    사용자 메시지 저장 → AI 파이프라인 실행 → 응답 메시지 저장.

    프론트 요청 예시:
        POST /chats/1/messages
        {
            "chat_room_id": 1,
            "role": "user",
            "model_type": "simple",
            "content": "건성 피부에 맞는 수분크림 추천해줘"
        }

    이미지 포함 예시:
        {
            "chat_room_id": 1,
            "role": "user",
            "model_type": "detailed",
            "image_url": ["https://s3.../img1.jpg", "https://s3.../img2.jpg"]
        }

    응답:
        [
            { "message_id": 5, "role": "user",      "content": "건성 피부에...", ... },
            { "message_id": 6, "role": "assistant",  "content": "세라마이드가 풍부한...", ... }
        ]
    """
    # 채팅방 소유권 확인
    room = chat_service.get_chat_room_by_id(chat_room_id)
    if not room:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    if room.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 1. 사용자 메시지 저장
    try:
        user_msg = chat_service.save_message(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 첫 메시지이면 채팅방 제목 자동 설정
    if not room.title and body.content:
        title = body.content[:30] + ("..." if len(body.content) > 30 else "")
        chat_service.update_chat_room_title(chat_room_id, title)

    # 2. AI 파이프라인 실행 (TODO: 실제 ai.orchestrator.pipeline 연동)
    # from ai.orchestrator.pipeline import run
    # ai_response_text = run(
    #     user_message = body.content,
    #     image_urls   = body.image_url,
    #     history      = chat_service.get_messages_by_room(chat_room_id),
    # )
    ai_response_text = "[AI 응답 예시] 건성 피부에는 세라마이드 함유 보습크림을 추천드립니다."

    # 3. AI 응답 메시지 저장
    ai_msg_data = MessageCreate(
        chat_room_id = chat_room_id,
        role         = "assistant",
        model_type   = body.model_type,
        content      = ai_response_text,
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

    프론트 요청 예시:
        GET /chats/1/messages             전체 조회
        GET /chats/1/messages?role=user   사용자 메시지만 조회
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
