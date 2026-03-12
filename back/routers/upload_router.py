import os
import uuid
import boto3

from .deps import get_current_user_id
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

"""
upload_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    POST   /upload    이미지 파일을 S3에 업로드하고 URL 반환
─────────────────────────────────────────────────────────────
필요한 환경변수 (.env):
    AWS_REGION
    S3_BUCKET_NAME
─────────────────────────────────────────────────────────────
"""

router = APIRouter(prefix="/upload", tags=["Upload"])

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("AWS_REGION", "ap-northeast-2")

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}     # 지원 이미지 확장자
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# 분석 유형 → S3 폴더 매핑
FOLDER_MAP = {
    "simple"    : "skin-analysis",
    "detailed"  : "skin-analysis",
    "ingredient": "ingredient-analysis",
    "profile"   : "profile",
}

# 자격증명
def _get_s3_client():
    return boto3.client("s3", region_name=S3_REGION)


# ─────────────────────────────────────────────
# 이미지 업로드
# ─────────────────────────────────────────────

@router.post("")
def upload_image(
    file          : UploadFile = File(...),
    analysis_type : str        = Query(default="quick"),
    user_id       : int        = Depends(get_current_user_id),
):
    """
    이미지 파일을 S3에 업로드하고 퍼블릭 URL 반환.

    S3 경로: {user_id}/skin-analysis/{uuid}.ext
            {user_id}/ingredient-analysis/{uuid}.ext

    프론트 요청 예시:
        POST /upload?analysis_type=quick
        Content-Type: multipart/form-data
        Body: file=<이미지 파일>

    응답:
        { "url": "https://<bucket>.s3.<region>.amazonaws.com/{user_id}/skin-analysis/..." }
    """

    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME 환경변수가 설정되지 않았습니다.")

    # 파일 타입 검증
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # 파일 크기 검증
    contents = file.file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다.")

    file.file.seek(0)  # 포인터 리셋

    # S3 키 생성
    folder = FOLDER_MAP.get(analysis_type, "other")
    ext    = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
    # profile은 고정 파일명, 나머지는 uuid
    filename = "profile" if analysis_type == "profile" else str(uuid.uuid4())
    s3_key   = f"{user_id}/{folder}/{filename}.{ext}"

    try:
        s3 = _get_s3_client()
        s3.upload_fileobj(
            file.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": file.content_type},
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 업로드 실패: {e.response['Error']['Message']}")

    s3_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

    return {"url": s3_url}
