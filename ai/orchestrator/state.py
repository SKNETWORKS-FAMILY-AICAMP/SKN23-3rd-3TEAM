"""
state.py
LangGraph에서 노드 간 공유되는 전체 상태를 정의합니다.

pipeline.py에서 함수 인자/로컬 변수로 흩어져 있던 중간 상태들을
GraphState 하나로 통합합니다.

흐름:
  START
  → route_node       : intent, needs_rag, needs_product 결정
  → context_node     : user_profile 로드
  → vision_node      : 이미지 분석 (분석 intent만)
  → search_node      : RAG + Tavily 병렬 실행
  → llm_node         : 답변 생성
  → validate_node    : 응답 검증 + 올리브영 링크 반영
  → END
"""
from __future__ import annotations
from typing import Any
from typing_extensions import TypedDict

from ai.orchestrator.router import RouteDecision


class GraphState(TypedDict, total=False):
    # ── 입력 (run() 호출 시 세팅) ───────────────────────────
    user_text: str
    images: list[bytes]
    analysis_type: str | None        # "quick" | "detailed" | "ingredient" | None
    user_id: int | None
    chat_history: list[dict]
    is_first_message: bool
    image_urls: list               # S3 업로드 URL (validate_node DB 저장용)

    # ── route_node 출력 ─────────────────────────────────────
    route: RouteDecision             # intent + needs_rag/needs_product/needs_context_check
    instant_response: dict | None    # greeting/out_of_domain 등 즉시 반환 응답

    # ── context_node 출력 ───────────────────────────────────
    user_profile: dict | None        # skin_type_label, skin_concern 등

    # ── vision_node 출력 ────────────────────────────────────
    vision_result: dict | None       # 피부 분석 결과

    # ── search_node 출력 ────────────────────────────────────
    rag_passages: list[dict]         # 벡터DB 검색 결과
    oliveyoung_products: list[dict]  # Tavily 올리브영 검색 결과

    # ── llm_node 출력 ───────────────────────────────────────
    llm_output: dict                 # LLM 원본 응답 (validate 전)

    # ── context_node 추가 출력 ───────────────────────────────
    guest_upsell: bool               # 비로그인 회원가입 유도 플래그

    # ── validate_node 출력 (최종 응답) ──────────────────────
    report: dict                     # 검증 완료 + 올리브영 링크 반영된 최종 응답
