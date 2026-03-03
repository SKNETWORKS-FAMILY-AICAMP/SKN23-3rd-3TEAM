"""
nodes/vision.py
이미지를 받아 fast_inference 또는 deep_inference를 실행합니다.

분석 모드:
  - quick(빠른 분석):    정면 1장 → predict_fast()  → skin_type, scores
  - detailed(정밀 분석): 정면+좌+우 3장 → predict_deep() → measurements, grades, reliability

이미지 전달 방식:
  - bytes 리스트로 받음 (Streamlit: st.file_uploader / FastAPI: UploadFile)
  - 임시 파일로 저장 후 모델에 경로 전달 → 분석 후 임시 파일 삭제

[추가] GPT Vision 얼굴 검증:
  - 모델 추론 전에 GPT-4o mini로 사람 얼굴 여부 확인
  - fast: 정면 얼굴 1장인지 확인
  - detailed: 좌측/정면/우측 얼굴 3장이 순서대로인지 확인
  - 검증 실패 시 모델 추론 없이 즉시 오류 응답 반환
"""
import os
import time
import base64
import tempfile

from ai.orchestrator.state import GraphState


# ── GPT Vision 얼굴 검증 ───────────────────────────────────────

def _encode_image_b64(image_bytes: bytes) -> str:
    """이미지 bytes → base64 문자열"""
    return base64.b64encode(image_bytes).decode("utf-8")


def _validate_face_images(images: list, mode: str) -> dict:
    """
    GPT-4o mini로 이미지가 올바른 얼굴 사진인지 검증합니다.

    Args:
        images: bytes 리스트
        mode: "quick" | "detailed"

    Returns:
        {"valid": True} 또는
        {"valid": False, "reason": "user에게 보여줄 메시지"}
    """
    from openai import OpenAI
    from ai.config.settings import OPENAI_API_KEY
    import json

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        if mode == "quick":
            # 빠른 분석: 정면 얼굴 1장 확인
            b64 = _encode_image_b64(images[0])
            prompt = (
                "이 이미지가 사람의 얼굴 사진인지 판단해주세요.\n"
                "반드시 아래 JSON 형식으로만 답변하세요:\n"
                '{"is_face": true/false, "reason": "간단한 이유"}\n\n'
                "판단 기준:\n"
                "- is_face: true → 사람 얼굴이 명확하게 찍힌 사진\n"
                "- is_face: false → 얼굴이 없거나, 동물, 사물, 풍경 등 다른 사진"
            )
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}",
                        "detail": "low"
                    }},
                ]
            }]

        else:
            # 정밀 분석: 좌측/정면/우측 3장 순서 확인
            b64_list = [_encode_image_b64(img) for img in images[:3]]
            prompt = (
                "3장의 이미지가 피부 분석용 얼굴 사진인지, 그리고 순서가 올바른지 판단해주세요.\n"
                "업로드 순서: 첫 번째=정면, 두 번째=좌측, 세 번째=우측\n\n"
                "반드시 아래 JSON 형식으로만 답변하세요:\n"
                '{"is_face": true/false, "order_correct": true/false, "reason": "간단한 이유"}\n\n'
                "판단 기준:\n"
                "- is_face: true → 3장 모두 사람 얼굴 사진\n"
                "- is_face: false → 얼굴이 아닌 사진이 1장이라도 있음\n"
                "- order_correct: true → 첫번째는 얼굴 정면, 두번째는 얼굴 좌측면, 세번째는 얼굴 우측면\n"
                "- order_correct: false → 순서가 맞지 않거나 판단 불가\n"
                "- is_face가 false면 order_correct는 false로 설정"
            )
            content = [{"type": "text", "text": prompt}]
            for b64 in b64_list:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}",
                        "detail": "low"
                    }
                })
            messages = [{"role": "user", "content": content}]

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=100,
            temperature=0,
            response_format={"type": "json_object"},
        )

        result = json.loads(resp.choices[0].message.content)
        print(f"[VISION QC] GPT 검증 결과: {result}", flush=True)

        if not result.get("is_face", False):
            return {
                "valid": False,
                "reason": (
                    "사람 얼굴 사진이 아닌 것 같아요 😊\n\n"
                    "피부 분석을 위해 얼굴이 잘 보이는 사진으로 다시 올려주세요.\n"
                    "- 정면을 바라보는 얼굴 사진\n"
                    "- 얼굴 전체가 화면에 나오도록\n"
                    "- 밝은 조명에서 촬영한 사진"
                )
            }

        if mode == "detailed" and not result.get("order_correct", False):
            return {
                "valid": False,
                "reason": (
                    "사진 순서가 올바르지 않은 것 같아요 😊\n\n"
                    "정밀 분석은 아래 순서로 업로드해주세요:\n"
                    "1️⃣ 얼굴 정면\n"
                    "2️⃣ 얼굴 좌측면 (왼쪽)\n"
                    "3️⃣ 얼굴 우측면 (오른쪽)"
                )
            }

        return {"valid": True}

    except Exception as e:
        # GPT 검증 실패 시 통과시킴 (서비스 중단 방지)
        print(f"[VISION QC] 검증 오류 → 스킵: {repr(e)}", flush=True)
        return {"valid": True}


# ── 임시 파일 헬퍼 ────────────────────────────────────────────

def _bytes_to_tempfile(image_bytes: bytes, suffix: str = ".jpg") -> str:
    """이미지 bytes를 임시 파일로 저장하고 경로를 반환합니다."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(image_bytes)
    except Exception:
        os.close(fd)
        raise
    return path


def _cleanup(paths: list):
    """임시 파일 삭제"""
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def _get_fast_predict():
    from skin_ai.fast_inference import predict_fast
    return predict_fast


def _get_deep_predict():
    from skin_ai.deep_inference import predict_deep
    return predict_deep


# ── 메인 노드 ────────────────────────────────────────────────

def vision_node(state: GraphState) -> GraphState:
    """
    [vision_node]
    입력: images (list[bytes]), analysis_type, route
    출력: vision_result

    vision_result 구조:
      빠른 분석: {"mode": "fast", "skin_metrics": {...}}
      정밀 분석: {"mode": "deep", "measurements": {...}, "grades": {...}, "reliability": {...}}
      오류:      {"mode": "error", "error": "...", "qc": {"status": "fail", "reason": "..."}}
    """
    route = state["route"]
    images = state.get("images", [])
    analysis_type = state.get("analysis_type")

    # Vision 불필요하면 스킵
    if not getattr(route, "needs_vision", False):
        return {"vision_result": None}

    if not images:
        print("[VISION] 이미지 없음 → 스킵", flush=True)
        return {"vision_result": {
            "mode": "error",
            "error": "이미지가 없어요. 사진을 업로드해주세요.",
            "qc": {"status": "fail", "reason": "no_image"}
        }}

    t0 = time.perf_counter()
    temp_paths = []
    vision_result = {}

    try:
        if analysis_type == "quick":
            if len(images) < 1:
                raise ValueError("빠른 분석에는 정면 사진 1장이 필요해요.")

            # [GPT 얼굴 검증]
            print("[VISION QC] 얼굴 사진 검증 중...", flush=True)
            qc = _validate_face_images(images, mode="quick")
            if not qc["valid"]:
                print(f"[VISION QC] 검증 실패 → 분석 중단", flush=True)
                return {"vision_result": {
                    "mode": "error",
                    "error": qc["reason"],
                    "qc": {"status": "fail", "reason": "invalid_image"}
                }}

            print("[VISION] 빠른 분석 시작 (fast_model, 1장)", flush=True)
            path_F = _bytes_to_tempfile(images[0])
            temp_paths.append(path_F)

            predict_fast = _get_fast_predict()
            vision_result = predict_fast(path_F)
            print(f"[VISION] 완료: skin_metrics={list(vision_result.get('skin_metrics', {}).keys())}", flush=True)

        elif analysis_type == "detailed":
            if len(images) < 3:
                raise ValueError(
                    f"정밀 분석에는 정면/좌/우 사진 3장이 필요해요. "
                    f"현재 {len(images)}장 받았어요."
                )

            # [GPT 얼굴 검증 + 순서 확인]
            print("[VISION QC] 얼굴 사진 및 순서 검증 중...", flush=True)
            qc = _validate_face_images(images, mode="detailed")
            if not qc["valid"]:
                print(f"[VISION QC] 검증 실패 → 분석 중단", flush=True)
                return {"vision_result": {
                    "mode": "error",
                    "error": qc["reason"],
                    "qc": {"status": "fail", "reason": "invalid_image"}
                }}

            print("[VISION] 정밀 분석 시작 (deep_model, 3장)", flush=True)
            # 프론트 업로드 순서: [0]=정면, [1]=좌측, [2]=우측
            # deep_inference 입력 순서: img_F=정면, img_L=좌측, img_R=우측 → 동일
            path_F = _bytes_to_tempfile(images[0])  # 정면
            path_L = _bytes_to_tempfile(images[1])  # 좌측
            path_R = _bytes_to_tempfile(images[2])  # 우측
            temp_paths.extend([path_F, path_L, path_R])

            predict_deep = _get_deep_predict()
            vision_result = predict_deep(img_F=path_F, img_L=path_L, img_R=path_R)
            n = len(vision_result.get("measurements", {}))
            print(f"[VISION] 완료: {n}개 지표", flush=True)

        elif analysis_type == "ingredient":
            if len(images) < 1:
                raise ValueError("성분 분석에는 화장품 성분표 사진 1장이 필요해요.")

            print("[VISION] 성분 분석 시작 (데모 모드)", flush=True)

            # ── 데모용: 미리 추출된 전성분 JSON에서 순서대로 반환 ──
            import json
            import hashlib

            demo_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "..", "skin_ai", "ingredient_demo"
            )
            demo_json_path = os.path.join(demo_dir, "demo_products.json")

            if os.path.exists(demo_json_path):
                with open(demo_json_path, "r", encoding="utf-8") as f:
                    demo_products = json.load(f)

                # 카운터 파일로 순서 추적 (1번째 호출→0, 2번째→1, 3번째→2, 다시→0)
                counter_path = os.path.join(demo_dir, ".demo_counter")
                try:
                    with open(counter_path, "r") as f:
                        idx = int(f.read().strip()) % len(demo_products)
                except (FileNotFoundError, ValueError):
                    idx = 0

                # 다음 호출을 위해 카운터 증가
                with open(counter_path, "w") as f:
                    f.write(str(idx + 1))

                product = demo_products[idx]
                print(
                    f"[VISION] 데모 제품 매칭: [{idx}] {product['product_name']} "
                    f"({len(product['ingredients'])}개 성분)",
                    flush=True,
                )

                vision_result = {
                    "mode": "ingredient",
                    "product_name": product.get("product_name", ""),
                    "brand": product.get("brand", ""),
                    "ingredients": product.get("ingredients", []),
                    "ingredient_count": len(product.get("ingredients", [])),
                    "source": "demo",
                }
            else:
                print(f"[VISION] 데모 JSON 없음: {demo_json_path}", flush=True)
                raise FileNotFoundError(
                    "성분 분석 모델을 사용할 수 없어요. 관리자에게 문의해주세요."
                )

        else:
            raise ValueError(f"알 수 없는 analysis_type: {analysis_type}")

    except FileNotFoundError as e:
        msg = str(e)
        print(f"[VISION ERROR] 체크포인트 없음: {msg}", flush=True)
        vision_result = {
            "mode": "error",
            "error": "모델 파일을 찾을 수 없어요. 관리자에게 문의해주세요.",
            "qc": {"status": "fail", "reason": "checkpoint_not_found"}
        }
    except ValueError as e:
        msg = str(e)
        print(f"[VISION ERROR] 입력 오류: {msg}", flush=True)
        vision_result = {
            "mode": "error",
            "error": msg,
            "qc": {"status": "fail", "reason": "invalid_input"}
        }
    except Exception as e:
        msg = repr(e)
        print(f"[VISION ERROR] 추론 실패: {msg}", flush=True)
        vision_result = {
            "mode": "error",
            "error": "분석 중 오류가 발생했어요. 다시 시도해주세요.",
            "qc": {"status": "fail", "reason": "inference_error", "detail": msg}
        }
    finally:
        _cleanup(temp_paths)

    print(f"[TIMER] vision_node: {time.perf_counter()-t0:.3f}s", flush=True)
    return {"vision_result": vision_result}
