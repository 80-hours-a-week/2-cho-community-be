"""session_models: 세션 관련 데이터 모델 및 함수 모듈.

사용자 세션 관리를 위한 함수들을 제공합니다.
"""

from datetime import datetime

from database.connection import get_connection


async def create_session(user_id: int, session_id: str, expires_at: datetime) -> None:
    """사용자 세션을 생성합니다.

    Args:
        user_id: 사용자 ID.
        session_id: 세션 ID.
        expires_at: 만료 시간.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_session (user_id, session_id, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, session_id, expires_at),
            )


async def get_session(session_id: str) -> dict | None:
    """세션 ID로 세션 정보를 조회합니다.

    Args:
        session_id: 세션 ID.

    Returns:
        세션 정보 딕셔너리, 없으면 None.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, session_id, expires_at
                FROM user_session
                WHERE session_id = %s
                """,
                (session_id,),
            )
            row = await cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "session_id": row[2],
                    "expires_at": row[3],
                }
            return None


async def delete_session(session_id: str) -> None:
    """세션을 삭제합니다.

    Args:
        session_id: 세션 ID.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM user_session WHERE session_id = %s
                """,
                (session_id,),
            )


async def delete_user_sessions(user_id: int) -> None:
    """특정 사용자의 모든 세션을 삭제합니다.

    Args:
        user_id: 사용자 ID.
    """
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM user_session WHERE user_id = %s
                """,
                (user_id,),
            )
