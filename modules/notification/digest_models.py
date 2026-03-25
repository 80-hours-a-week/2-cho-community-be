"""digest_models: 다이제스트 이메일용 데이터 쿼리.

직접 SQL 쿼리를 사용하여 순환 import를 방지합니다.
다른 모듈의 model 함수를 import하지 않습니다.
"""

import logging

from core.database.connection import get_cursor

logger = logging.getLogger(__name__)


async def get_eligible_users(frequency: str, lookback_days: int) -> list[dict]:
    """다이제스트 수신 대상 사용자 조회.

    조건:
    - digest_frequency 일치 (설정 행이 없으면 기본값 'weekly')
    - 비활성 (lookback 기간 내 post_view_log 없음)
    - 이메일 인증 완료
    - 정지되지 않음
    - 탈퇴하지 않음
    """
    async with get_cursor() as cur:
        await cur.execute(
            """
            SELECT u.id, u.email, u.nickname
            FROM user u
            LEFT JOIN notification_setting ns ON u.id = ns.user_id
            WHERE COALESCE(ns.digest_frequency, 'weekly') = %s
              AND u.email_verified = 1
              AND u.deleted_at IS NULL
              AND (u.suspended_until IS NULL OR u.suspended_until < NOW())
              AND NOT EXISTS (
                  SELECT 1 FROM post_view_log pvl
                  WHERE pvl.user_id = u.id
                    AND pvl.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
              )
            """,
            (frequency, lookback_days),
        )
        return await cur.fetchall()


async def get_top_posts(lookback_days: int, limit: int = 5) -> list[dict]:
    """기간 내 인기 게시글 (hot score 기준).

    Returns:
        [{id, title, likes, comments}] 형태의 딕셔너리 리스트.
    """
    async with get_cursor() as cur:
        await cur.execute(
            """
            SELECT
                p.id,
                p.title,
                COALESCE(lk.cnt, 0) AS likes,
                COALESCE(cm.cnt, 0) AS comments,
                (COALESCE(lk.cnt, 0) * 3
                 + COALESCE(cm.cnt, 0) * 2
                 + p.views * 0.5)
                / POW(TIMESTAMPDIFF(HOUR, p.created_at, NOW()) + 2, 1.5) AS hot_score
            FROM post p
            LEFT JOIN (
                SELECT post_id, COUNT(*) AS cnt
                FROM post_like
                GROUP BY post_id
            ) lk ON lk.post_id = p.id
            LEFT JOIN (
                SELECT post_id, COUNT(*) AS cnt
                FROM comment
                WHERE deleted_at IS NULL
                GROUP BY post_id
            ) cm ON cm.post_id = p.id
            WHERE p.deleted_at IS NULL
              AND p.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY hot_score DESC
            LIMIT %s
            """,
            (lookback_days, limit),
        )
        rows = await cur.fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "likes": row["likes"],
            "comments": row["comments"],
        }
        for row in rows
    ]


async def get_following_posts(user_id: int, lookback_days: int, limit: int = 3) -> list[dict]:
    """팔로잉 사용자의 새 게시글.

    Returns:
        [{id, title, nickname}] 형태의 딕셔너리 리스트.
    """
    async with get_cursor() as cur:
        await cur.execute(
            """
            SELECT p.id, p.title, u.nickname
            FROM post p
            JOIN user u ON p.author_id = u.id
            JOIN user_follow uf ON uf.following_id = p.author_id
                                AND uf.follower_id = %s
            WHERE p.deleted_at IS NULL
              AND p.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY p.created_at DESC
            LIMIT %s
            """,
            (user_id, lookback_days, limit),
        )
        rows = await cur.fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "nickname": row["nickname"],
        }
        for row in rows
    ]


async def get_unread_notification_count(user_id: int) -> int:
    """읽지 않은 알림 수."""
    async with get_cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) AS cnt FROM notification WHERE user_id = %s AND is_read = 0",
            (user_id,),
        )
        row = await cur.fetchone()
        return row["cnt"] if row else 0


async def get_subscription_update_count(user_id: int, lookback_days: int) -> int:
    """구독 중인 게시글의 새 댓글 수 (자신의 댓글 제외)."""
    async with get_cursor() as cur:
        await cur.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM comment c
            JOIN post_subscription ps ON ps.post_id = c.post_id
                                      AND ps.user_id = %s
                                      AND ps.level = 'watching'
            WHERE c.deleted_at IS NULL
              AND c.author_id != %s
              AND c.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (user_id, user_id, lookback_days),
        )
        row = await cur.fetchone()
        return row["cnt"] if row else 0
