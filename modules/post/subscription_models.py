"""subscription_models: 게시글 구독 DB 레이어.

post_subscription 테이블에 대한 CRUD 및 조회 함수를 제공합니다.
"""

from typing import Literal

from core.database.connection import get_cursor, transactional

SubscriptionLevel = Literal["watching", "normal", "muted"]


async def get_subscription_level(user_id: int, post_id: int) -> SubscriptionLevel:
    """사용자의 게시글 구독 수준을 반환합니다. 행이 없으면 'normal'."""
    async with get_cursor() as cur:
        await cur.execute(
            "SELECT level FROM post_subscription WHERE user_id = %s AND post_id = %s",
            (user_id, post_id),
        )
        row = await cur.fetchone()
    return row["level"] if row else "normal"


async def set_subscription(user_id: int, post_id: int, level: SubscriptionLevel) -> None:
    """구독 수준을 설정합니다. 이미 존재하면 업데이트합니다."""
    async with transactional() as cur:
        await cur.execute(
            """
            INSERT INTO post_subscription (user_id, post_id, level)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE level = VALUES(level)
            """,
            (user_id, post_id, level),
        )


async def delete_subscription(user_id: int, post_id: int) -> None:
    """구독 행을 삭제하여 기본 상태(normal)로 되돌립니다."""
    async with transactional() as cur:
        await cur.execute(
            "DELETE FROM post_subscription WHERE user_id = %s AND post_id = %s",
            (user_id, post_id),
        )


async def auto_subscribe(user_id: int, post_id: int) -> None:
    """자동 구독 (watching). 기존 행이 있으면 덮어쓰지 않습니다."""
    async with transactional() as cur:
        await cur.execute(
            """
            INSERT IGNORE INTO post_subscription (user_id, post_id, level)
            VALUES (%s, %s, 'watching')
            """,
            (user_id, post_id),
        )


async def get_watching_user_ids(post_id: int) -> list[int]:
    """게시글을 watching 중인 사용자 ID 목록을 반환합니다."""
    async with get_cursor() as cur:
        await cur.execute(
            "SELECT user_id FROM post_subscription WHERE post_id = %s AND level = 'watching'",
            (post_id,),
        )
        rows = await cur.fetchall()
    return [row["user_id"] for row in rows]


async def get_user_watching_post_ids(user_id: int, post_ids: list[int]) -> set[int]:
    """주어진 게시글 목록 중 사용자가 watching 중인 게시글 ID 집합을 반환합니다."""
    if not post_ids:
        return set()
    placeholders = ",".join(["%s"] * len(post_ids))
    async with get_cursor() as cur:
        await cur.execute(
            f"SELECT post_id FROM post_subscription "
            f"WHERE user_id = %s AND level = 'watching' AND post_id IN ({placeholders})",
            (user_id, *post_ids),
        )
        rows = await cur.fetchall()
    return {row["post_id"] for row in rows}
