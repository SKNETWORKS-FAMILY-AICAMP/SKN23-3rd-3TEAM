"""
email_service.py
─────────────────────────────────────────────────────────────
목적  : 이메일 OTP 생성/검증 및 SendGrid 발송
역할  :
    - HMAC-SHA256 기반 무상태 OTP 생성 (DB 저장 없음)
    - OTP 유효성 검증 (현재 + 이전 윈도우, 최대 10~20분)
    - SendGrid API로 인증 이메일 발송

의존성:
    pip install sendgrid
─────────────────────────────────────────────────────────────
"""

import hmac
import hashlib
import time
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# ─────────────────────────────────────────────
# OTP 생성 / 검증
# ─────────────────────────────────────────────

def generate_otp(email: str, secret: str, window_minutes: int = 10) -> str:
    """
    HMAC-SHA256 기반 6자리 OTP 생성.

    - window: 현재 시각을 window_minutes(초)로 나눈 몫 (시간 구간)
    - 같은 구간 내에서는 항상 동일한 코드 생성

    사용 예시:
        otp = generate_otp("user@example.com", os.getenv("EMAIL_OTP_SECRET"))
    """
    window = int(time.time()) // (window_minutes * 60)
    msg = f"{email}:{window}".encode()
    h = hmac.new(secret.encode(), msg, hashlib.sha256)
    return str(int(h.hexdigest(), 16))[-6:].zfill(6)


def verify_otp(email: str, code: str, secret: str, window_minutes: int = 10) -> bool:
    """
    OTP 검증.

    - 현재 윈도우 + 이전 윈도우 총 2개 검증 (최대 10~20분 유효)
    - hmac.compare_digest 사용 (타이밍 공격 방어)

    사용 예시:
        ok = verify_otp("user@example.com", "123456", os.getenv("EMAIL_OTP_SECRET"))
    """
    for delta in [0, -1]:   # 현재 윈도우 → 이전 윈도우 순서로 검증
        window = int(time.time()) // (window_minutes * 60) + delta
        msg = f"{email}:{window}".encode()
        h = hmac.new(secret.encode(), msg, hashlib.sha256)
        expected = str(int(h.hexdigest(), 16))[-6:].zfill(6)
        if hmac.compare_digest(code, expected):
            return True
    return False


# ─────────────────────────────────────────────
# SendGrid 이메일 발송
# ─────────────────────────────────────────────

def send_verification_email(email: str, otp: str) -> None:
    """
    SendGrid API로 인증 이메일 발송.

    필요한 환경변수:
        SENDGRID_API_KEY      : SendGrid API Key
        SENDGRID_FROM_EMAIL   : SendGrid에 등록된 발신자 이메일

    사용 예시:
        send_verification_email("user@example.com", "123456")
    """
    api_key    = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")

    if not api_key or not from_email:
        raise RuntimeError(
            "SENDGRID_API_KEY 또는 SENDGRID_FROM_EMAIL 환경변수가 설정되지 않았습니다."
        )

    message = Mail(
        from_email   = from_email,
        to_emails    = email,
        subject      = "[AI 피부 분석 챗봇] 이메일 인증 코드",
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 2rem;">
            <h2 style="color: #84c13d;">이메일 인증</h2>
            <p>아래 6자리 코드를 입력하세요. 코드는 <strong>10분</strong> 동안 유효합니다.</p>
            <div style="
                font-size: 2.5rem;
                font-weight: bold;
                letter-spacing: 0.8rem;
                color: #84c13d;
                background: #F5F3FF;
                padding: 1rem 2rem;
                border-radius: 8px;
                display: inline-block;
                margin: 1rem 0;
            ">
                {otp}
            </div>
            <p style="color: #6B7280; margin-top: 1.5rem; font-size: 0.875rem;">
                본인이 요청하지 않은 경우 이 이메일을 무시하세요.
            </p>
        </div>
        """,
    )

    sg = SendGridAPIClient(api_key)
    response = sg.send(message)

    if response.status_code not in (200, 202):
        raise RuntimeError(
            f"이메일 발송 실패 (HTTP {response.status_code}): {response.body}"
        )
