"""digest_service: 다이제스트 이메일 발송 서비스.

daily는 매일, weekly는 일요일(UTC)에만 발송합니다.
"""

import logging
from datetime import UTC, datetime

from core.config import settings
from core.utils.email import send_email
from core.utils.email_templates import build_digest_html, build_digest_text
from modules.notification.digest_models import (
    get_eligible_users,
    get_following_posts,
    get_subscription_update_count,
    get_top_posts,
    get_unread_notification_count,
)

logger = logging.getLogger(__name__)

# 주파수별 lookback 기간 (일)
_LOOKBACK = {"daily": 1, "weekly": 7}


async def send_digests() -> dict:
    """다이제스트 발송. daily는 매일, weekly는 일요일(UTC)에만.

    Returns:
        {"daily": 발송 수, "weekly": 발송 수, "errors": 오류 수}
    """
    results: dict[str, int] = {"daily": 0, "weekly": 0, "errors": 0}
    is_sunday = datetime.now(UTC).weekday() == 6

    frequencies = ["daily"]
    if is_sunday:
        frequencies.append("weekly")

    site_url = settings.FRONTEND_URL

    for freq in frequencies:
        lookback = _LOOKBACK[freq]
        users = await get_eligible_users(freq, lookback)

        # 전체 인기 게시글은 주파수별 1회만 조회
        top_posts = await get_top_posts(lookback, limit=5)

        for user in users:
            try:
                user_id = user["id"]

                following_posts = await get_following_posts(user_id, lookback, limit=3)
                unread_count = await get_unread_notification_count(user_id)
                subscription_updates = await get_subscription_update_count(user_id, lookback)

                # 콘텐츠가 전혀 없으면 발송 스킵
                if not top_posts and not following_posts and unread_count == 0:
                    continue

                html_body = build_digest_html(
                    top_posts=top_posts,
                    following_posts=following_posts,
                    unread_count=unread_count,
                    subscription_updates=subscription_updates,
                    site_url=site_url,
                )
                text_body = build_digest_text(
                    top_posts=top_posts,
                    following_posts=following_posts,
                    unread_count=unread_count,
                    subscription_updates=subscription_updates,
                    site_url=site_url,
                )

                subject = "Camp Linux 주간 다이제스트" if freq == "weekly" else "Camp Linux 일간 다이제스트"
                await send_email(
                    to=user["email"],
                    subject=subject,
                    body=text_body,
                    html_body=html_body,
                )
                results[freq] += 1

            except Exception:
                logger.exception(
                    "다이제스트 발송 실패 (user_id=%s, freq=%s)",
                    user.get("id"),
                    freq,
                )
                results["errors"] += 1

    logger.info("다이제스트 발송 완료: %s", results)
    return results
