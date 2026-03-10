"""
wishlist_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    GET    /wishlist              사용자 위시리스트 조회
    GET    /wishlist/{wish_id}    위시리스트 단건 조회
    POST   /wishlist              위시리스트 추가
    DELETE /wishlist/{wish_id}    위시리스트 삭제
─────────────────────────────────────────────────────────────
"""

from .deps import get_current_user_id
from services import analysis_service
from db.schemas import WishlistAdd, WishlistResponse
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get("", response_model=list[WishlistResponse])
def get_wishlist(user_id: int = Depends(get_current_user_id)):
    """
    사용자별 위시리스트 조회

    프론트 요청 예시:
        GET /wishlist
    응답:
        [ { "wish_id": 3, "product_name": "...", ... }, ... ]
    """
    items = analysis_service.get_wishlist_by_user(user_id)
    return [_wish_to_response(w) for w in items]

@router.post("", response_model=WishlistResponse, status_code=201)
def add_to_wishlist(
    body    : WishlistAdd,
    user_id : int = Depends(get_current_user_id),
):
    """
    위시리스트에 제품 추가.
    동일 제품(product_vector_id)을 이미 추가했으면 400 반환.

    프론트 요청 예시:
        POST /wishlist
        {
            "user_id": 1,
            "product_vector_id": "vec_abc123",
            "product_name": "라로슈포제 시카플라스트 밤 B5",
            "message_id": 10,
            "product_description": "민감한 피부 진정 크림"
        }OnboardingPage
    응답:
        { "wish_id": 3, "user_id": 1, "product_name": "라로슈포제...", ... }
    """
    if body.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    try:
        wish = analysis_service.add_to_wishlist(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _wish_to_response(wish)

@router.delete("/{wish_id}", status_code=204)
def remove_from_wishlist(
    wish_id : int,
    user_id : int = Depends(get_current_user_id),
):
    """
    위시리스트 항목 삭제.
    본인 항목이 아니면 404 반환.

    프론트 요청 예시:
        DELETE /wishlist/3
    """
    success = analysis_service.remove_from_wishlist(wish_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="위시리스트 항목을 찾을 수 없습니다.")


# 내부 헬퍼
def _wish_to_response(wish) -> WishlistResponse:
    return WishlistResponse(
        wish_id             = wish.wish_id,
        user_id             = wish.user_id,
        product_vector_id   = wish.product_vector_id,
        product_name        = wish.product_name,
        product_description = wish.product_description,
        message_id          = wish.message_id,
        added_at            = wish.added_at,
    )