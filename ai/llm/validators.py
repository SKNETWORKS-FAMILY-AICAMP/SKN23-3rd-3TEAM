# -----------------------------------------------------------------------------
# Change Log
# - 2026-02-27: (bugfix) 도메인 밖 입력/근거 부족 시 LLM 출력이 정책을 깨며
#   ValueError로 Streamlit 앱이 중단되는 문제 해결.
#   - 기존: 정책 위반(문장수, citation 형식, recommendations empty) -> raise
#   - 변경: raise 대신 보정/필터링으로 "유효한 FinalReport"를 항상 반환
# -----------------------------------------------------------------------------
from ai.schemas.report_schema import FinalReport, Recommendation

def validate_report(report_dict) -> FinalReport:
    # 1) 기본 스키마 검증
    report = FinalReport.model_validate(report_dict)

    # 2) chat_answer 문장 수 정책: raise 대신 보정 (앱 크래시 방지)
    if report.chat_answer:
        sentences = [s.strip() for s in report.chat_answer.split(".") if s.strip()]
        if len(sentences) < 3:
            # 짧으면 3문장으로 늘리기(중복 없이)
            report.chat_answer = (
                report.chat_answer.strip()
                + " 피부 고민(예: 홍조/여드름/건조/모공)과 현재 루틴을 알려주면 더 정확히 안내할 수 있어요."
                + " 증상이 심하거나 통증/진물/급격한 악화가 있으면 피부과 상담을 권장해요."
            )
        elif len(sentences) > 6:
            # 길면 앞부분만 유지
            report.chat_answer = ". ".join(sentences[:6]) + "."

    # 3) citations: 형식 깨진 항목은 제거(raise 금지)
    if report.citations:
        report.citations = [c for c in report.citations if c.source_id and c.snippet]

    # 4) recommendations: 비면 기본값 주입
    if not report.recommendations:
        report.recommendations = [
            Recommendation(
                category="Lifestyle",
                items=["추가 정보가 부족해 일반적인 안내만 제공 가능합니다. 피부 고민을 구체적으로 알려주세요."]
            )
        ]
        # warnings가 None/빈 리스트일 수도 있으니 안전하게
        if report.warnings is None:
            report.warnings = []
        msg = "근거 부족 또는 도메인 불일치로 recommendations를 기본값으로 보정함"
        if msg not in report.warnings:
            report.warnings.append(msg)

    return report