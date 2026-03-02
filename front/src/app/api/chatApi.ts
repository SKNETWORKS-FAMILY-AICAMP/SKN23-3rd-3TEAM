/**
 * chatApi.ts
 * ─────────────────────────────────────────────────────────────
 * back/routers/chat_router.py 의 /chats 엔드포인트와 통신.
 *
 * 사용하는 엔드포인트:
 *   GET    /chats                           → fetchChatRooms()
 *   POST   /chats                           → createChatRoom()
 *   DELETE /chats/{chat_room_id}            → deleteChatRoom()
 *   GET    /chats/{chat_room_id}/messages   → fetchMessages()
 *   POST   /chats/{chat_room_id}/messages   → sendMessage()
 *   POST   /chats/guest/message             → sendGuestMessage()  (비로그인 전용)
 * ─────────────────────────────────────────────────────────────
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function getToken(): string {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("로그인이 필요합니다.");
  return token;
}

// ─────────────────────────────────────────────
// 타입 정의 (back/db/schemas.py 대응)
// ─────────────────────────────────────────────

export interface GuestMessageResponse {
  role   : string;
  content: string;
}

export interface ChatRoom {
  chat_room_id : number;
  user_id      : number;
  title        : string | null;
  created_at   : string;
}

export interface ChatMessage {
  message_id   : number;
  chat_room_id : number;
  role         : "user" | "assistant";
  model_type   : string;
  content      : string;
  image_url    : string[] | string | null;  // DB에 JSON 문자열로 저장된 경우 string으로 올 수 있음
  created_at   : string;
}

// ─────────────────────────────────────────────
// API 함수
// ─────────────────────────────────────────────

/**
 * 내 채팅방 목록 조회 (최신순).
 * back: GET /chats → chat_service.get_chat_rooms_by_user()
 */
export async function fetchChatRooms(): Promise<ChatRoom[]> {
  const res = await fetch(`${API_BASE}/chats`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
  return res.json() as Promise<ChatRoom[]>;
}

/**
 * 새 채팅방 생성.
 * back: POST /chats → chat_service.create_chat_room()
 */
export async function createChatRoom(): Promise<ChatRoom> {
  const res = await fetch(`${API_BASE}/chats`, {
    method  : "POST",
    headers : { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
  return res.json() as Promise<ChatRoom>;
}

/**
 * 채팅방 삭제 (soft delete).
 * back: DELETE /chats/{chat_room_id} → chat_service.delete_chat_room()
 */
export async function deleteChatRoom(chatRoomId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/chats/${chatRoomId}`, {
    method : "DELETE",
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
}

/**
 * 채팅방 메시지 내역 조회 (시간 오름차순).
 * back: GET /chats/{chat_room_id}/messages → chat_service.get_messages_by_room()
 */
export async function fetchMessages(chatRoomId: number): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE}/chats/${chatRoomId}/messages`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
  return res.json() as Promise<ChatMessage[]>;
}

/**
 * 비로그인 사용자 텍스트 채팅 (DB 저장 없음, 인증 불필요).
 * back: POST /chats/guest/message
 */
export async function sendGuestMessage(content: string): Promise<GuestMessageResponse> {
  const res = await fetch(`${API_BASE}/chats/guest/message`, {
    method  : "POST",
    headers : { "Content-Type": "application/json" },
    body    : JSON.stringify({ content }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
  return res.json() as Promise<GuestMessageResponse>;
}

/**
 * 메시지 전송 (AI 응답 포함 반환).
 * back: POST /chats/{chat_room_id}/messages → chat_service.save_message() + AI pipeline
 * 반환: [사용자메시지, AI응답메시지]
 */
export async function sendMessage(
  chatRoomId : number,
  body       : { content: string; model_type?: string; image_url?: string[] },
): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE}/chats/${chatRoomId}/messages`, {
    method  : "POST",
    headers : {
      Authorization  : `Bearer ${getToken()}`,
      "Content-Type" : "application/json",
    },
    body: JSON.stringify({
      chat_room_id : chatRoomId,
      role         : "user",
      ...(body.model_type && { model_type: body.model_type }),
      content      : body.content,
      image_url    : body.image_url ?? null,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
  return res.json() as Promise<ChatMessage[]>;
}
