"""
analysis_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    POST   /analysis                       피부 분석 결과 저장
    GET    /analysis                       내 분석 히스토리 조회
    GET    /analysis/latest                가장 최근 분석 결과 조회
    GET    /analysis/{analysis_id}         분석 결과 단건 조회
    DELETE /analysis/{analysis_id}         분석 결과 삭제 (soft delete)
─────────────────────────────────────────────────────────────
"""

from fastapi import APIRouter, HTTPException, Depends

from db.schemas import AnalysisCreate, AnalysisResponse, KeywordResponse
from services import analysis_service
from .deps import get_current_user_id

router = APIRouter(prefix="/analysis", tags=["Analysis"])


# ─────────────────────────────────────────────
# 피부 분석 결과
# ─────────────────────────────────────────────

@router.post("", response_model=AnalysisResponse, status_code=201)
def save_analysis(
    body    : AnalysisCreate,
    user_id : int = Depends(get_current_user_id),
):
    """
    피부 분석 결과 저장.
    image_url과 analysis_data를 받아 DB에 저장.

    프론트 요청 예시:
        POST /analysis
        {
            "user_id": 1,
            "image_url": ["https://s3.../face1.jpg"],
            "model_type": "simple",
            "analysis_data": { "moisture": 72, "oil": 45, "pore": 30 }
        }
    응답:
        { "analysis_id": 1, "user_id": 1, "model_type": "simple", ... }
    """
    if body.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    result = analysis_service.save_analysis(body)
    return _analysis_to_response(result)


@router.get("", response_model=list[AnalysisResponse])
def get_analysis_history(user_id: int = Depends(get_current_user_id)):
    """
    내 피부 분석 히스토리 전체 조회 (최신순).

    프론트 요청 예시:
        GET /analysis
    응답:
        [ { "analysis_id": 3, ... }, { "analysis_id": 1, ... } ]
    """
    results = analysis_service.get_analysis_history(user_id)
    return [_analysis_to_response(r) for r in results]


@router.get("/latest", response_model=AnalysisResponse)
def get_latest_analysis(user_id: int = Depends(get_current_user_id)):
    """
    가장 최근 피부 분석 결과 단건 조회.
    AI 파이프라인에서 사용자 피부 상태 컨텍스트 로드 시 활용.

    프론트 요청 예시:
        GET /analysis/latest
    응답:
        { "analysis_id": 5, "model_type": "detailed", ... }
    """
    result = analysis_service.get_latest_analysis(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="분석 결과가 없습니다.")
    return _analysis_to_response(result)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id : int,
    user_id     : int = Depends(get_current_user_id),
):
    """
    분석 결과 단건 조회.

    프론트 요청 예시:
        GET /analysis/1
    """
    result = analysis_service.get_analysis_by_id(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    if result.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return _analysis_to_response(result)


@router.delete("/{analysis_id}", status_code=204)
def delete_analysis(
    analysis_id : int,
    user_id     : int = Depends(get_current_user_id),
):
    """
    분석 결과 삭제 (soft delete).

    프론트 요청 예시:
        DELETE /analysis/1
    """
    result = analysis_service.get_analysis_by_id(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    if result.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    analysis_service.delete_analysis(analysis_id)




# ─────────────────────────────────────────────
# 피부 케어 루틴 키워드 (Factorial) 목록 조회
# ─────────────────────────────────────────────

@router.get("/factorials", response_model=list[KeywordResponse])
def get_factorials():
    """
    skin_care_routine 타입 키워드 전체 조회.
    - 프론트 분석 페이지의 factorial 선택지 표시용
    - AI 파이프라인 select_factorial() 내부 호출용

    인증 불필요 (공개 엔드포인트).

    프론트 요청 예시:
        GET /analysis/factorials
    응답:
        [
          {"keyword_id": 1, "keyword": "moisturizing_boost", "label": "보습 강화", ...},
          {"keyword_id": 2, "keyword": "oil_cleansing",      "label": "오일 클렌징", ...},
          ...
        ]
    """
    return analysis_service.get_skin_care_routines()

# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────

def _analysis_to_response(result) -> AnalysisResponse:
    img = result.image_url
    return AnalysisResponse(
        analysis_id   = result.analysis_id,
        user_id       = result.user_id,
        image_url     = img if isinstance(img, list) else img.split(","),
        model_type    = result.model_type,
        analysis_data = result.analysis_data,
        created_at    = result.created_at,
    )
