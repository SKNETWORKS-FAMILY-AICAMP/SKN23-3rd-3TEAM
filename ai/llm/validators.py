from ai.schemas.report_schema import FinalReport

def validate_report(report_dict) -> FinalReport:
    # Pydantic이 타입/필수필드/범위를 검사
    return FinalReport.model_validate(report_dict)