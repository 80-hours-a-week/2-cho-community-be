"""email: 이메일 발송 유틸리티.

로컬 개발: SMTP (settings.EMAIL_BACKEND = "smtp")
프로덕션(Lambda): AWS SES (settings.EMAIL_BACKEND = "ses")
환경변수 EMAIL_BACKEND로 전환.
"""

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import settings

logger = logging.getLogger(__name__)


def _send_via_smtp(to: str, subject: str, body: str, html_body: str | None = None) -> None:
    """SMTP로 이메일을 발송합니다 (동기 — asyncio.to_thread에서 호출).

    html_body가 제공되면 multipart/alternative로 HTML + 텍스트를 함께 발송합니다.
    """
    if html_body is not None:
        # HTML과 텍스트를 함께 포함하는 multipart/alternative 메시지
        msg: MIMEMultipart | MIMEText = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
    else:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


def _send_via_ses(to: str, subject: str, body: str, html_body: str | None = None) -> None:
    """AWS SES로 이메일을 발송합니다 (동기 — asyncio.to_thread에서 호출).

    Lambda 런타임에 boto3가 기본 포함되어 있으므로 조건부 import 사용.
    html_body가 제공되면 HTML 파트도 함께 포함합니다.
    """
    import boto3

    client = boto3.client("ses", region_name=settings.SES_REGION)

    email_body: dict = {"Text": {"Data": body, "Charset": "UTF-8"}}
    if html_body is not None:
        email_body["Html"] = {"Data": html_body, "Charset": "UTF-8"}

    client.send_email(
        Source=settings.EMAIL_FROM,
        Destination={"ToAddresses": [to]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": email_body,
        },
    )


async def send_email(to: str, subject: str, body: str, html_body: str | None = None) -> None:
    """이메일을 비동기로 발송합니다.

    EMAIL_BACKEND 설정에 따라 SES 또는 SMTP를 사용합니다.
    동기 I/O를 asyncio.to_thread로 실행하여 이벤트 루프 블로킹을 방지합니다.

    Args:
        to: 수신자 이메일 주소.
        subject: 이메일 제목.
        body: 이메일 텍스트 본문 (HTML 미지원 클라이언트 폴백).
        html_body: HTML 이메일 본문. 제공 시 multipart/alternative로 발송.

    Raises:
        RuntimeError: 이메일 발송 실패 시.
    """
    if settings.TESTING:
        logger.info("테스트 환경: 이메일 발송 스킵 (%s)", to)
        return

    backend = settings.EMAIL_BACKEND.lower()
    try:
        if backend == "ses":
            await asyncio.to_thread(_send_via_ses, to, subject, body, html_body)
        else:
            await asyncio.to_thread(_send_via_smtp, to, subject, body, html_body)
        logger.info(f"이메일 발송 성공: {to} (백엔드: {backend})")
    except Exception as e:
        logger.exception(f"이메일 발송 실패: {to}")
        raise RuntimeError(f"이메일 발송 실패: {e}") from e
