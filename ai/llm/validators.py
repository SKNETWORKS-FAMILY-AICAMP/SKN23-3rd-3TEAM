from ai.schemas.report_schema import FinalReport

# def validate_report(report_dict) -> FinalReport:
#     # Pydantic이 타입/필수필드/범위를 검사
#     return FinalReport.model_validate(report_dict)

def validate_report(report_dict) -> FinalReport:
    # 1️⃣ 기본 스키마 검증 (타입 / 필수필드 / 범위)
    report = FinalReport.model_validate(report_dict)

    # 2️⃣ chat_answer 문장 수 정책 (3~6문장)
    sentences = [s.strip() for s in report.chat_answer.split(".") if s.strip()]
    if not (3 <= len(sentences) <= 6):
        raise ValueError("chat_answer must be 3~6 sentences")

    # 3️⃣ citation 기본 형식 안전 검사 (비어있어도 OK)
    for c in report.citations:
        if not c.source_id or not c.snippet:
            raise ValueError("Invalid citation: source_id and snippet required")

    # 4️⃣ recommendations 비어있는 경우 방지
    if not report.recommendations:
        raise ValueError("recommendations must not be empty")

    return report