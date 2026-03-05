"""사용자 검색 및 통계 모델 함수 테스트."""

from unittest.mock import AsyncMock, patch

import pytest

from models.user_models import get_user_stats, search_users_by_nickname


def _make_async_cursor(fetchall_result=None, fetchone_result=None):
    """비동기 커서 mock 생성 헬퍼."""
    cursor = AsyncMock()
    cursor.execute = AsyncMock()
    cursor.fetchall = AsyncMock(return_value=fetchall_result or [])
    cursor.fetchone = AsyncMock(return_value=fetchone_result)
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=False)
    return cursor


def _make_async_conn(cursors):
    """비동기 커넥션 mock 생성 헬퍼. cursors 리스트를 순서대로 반환."""
    conn = AsyncMock()
    cursor_iter = iter(cursors)

    def cursor_factory():
        return next(cursor_iter)

    conn.cursor = cursor_factory
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    return conn


class TestSearchUsersByNickname:
    """닉네임 검색 모델 함수 테스트."""

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self):
        """빈 쿼리는 빈 리스트를 반환한다."""
        result = await search_users_by_nickname("", set())
        assert result == []

    @pytest.mark.asyncio
    async def test_whitespace_query_returns_empty(self):
        """공백만 있는 쿼리는 빈 리스트를 반환한다."""
        result = await search_users_by_nickname("   ", set())
        assert result == []

    @pytest.mark.asyncio
    @patch("models.user_models.get_connection")
    async def test_prefix_match_returns_results(self, mock_get_conn):
        """닉네임 접두어 검색이 올바른 결과를 반환한다."""
        rows = [
            (1, "alice", None),
            (2, "alice2", "/uploads/img.jpg"),
        ]
        cursor = _make_async_cursor(fetchall_result=rows)
        conn = _make_async_conn([cursor])
        mock_get_conn.return_value = conn

        result = await search_users_by_nickname("ali", set())

        assert len(result) == 2
        assert result[0]["user_id"] == 1
        assert result[0]["nickname"] == "alice"
        # None이면 기본 프로필 이미지
        assert result[0]["profileImageUrl"] == "/assets/profiles/default_profile.jpg"
        assert result[1]["profileImageUrl"] == "/uploads/img.jpg"

    @pytest.mark.asyncio
    @patch("models.user_models.get_connection")
    async def test_exclude_user_ids_applied(self, mock_get_conn):
        """제외 ID가 SQL에 반영된다."""
        cursor = _make_async_cursor(fetchall_result=[])
        conn = _make_async_conn([cursor])
        mock_get_conn.return_value = conn

        await search_users_by_nickname("test", {10, 20})

        call_args = cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "NOT IN" in sql
        # params: [query%, *exclude_ids, limit]
        assert params[0] == "test%"
        assert set(params[1:-1]) == {10, 20}


class TestGetUserStats:
    """사용자 활동 통계 조회 테스트."""

    @pytest.mark.asyncio
    @patch("models.user_models.get_connection")
    async def test_returns_correct_stats(self, mock_get_conn):
        """게시글, 댓글, 좋아요 수를 올바르게 반환한다."""
        cur_posts = _make_async_cursor(fetchone_result=(5,))
        cur_comments = _make_async_cursor(fetchone_result=(12,))
        cur_likes = _make_async_cursor(fetchone_result=(30,))

        conn = _make_async_conn([cur_posts, cur_comments, cur_likes])
        mock_get_conn.return_value = conn

        result = await get_user_stats(user_id=1)

        assert result == {
            "posts_count": 5,
            "comments_count": 12,
            "likes_received_count": 30,
        }

    @pytest.mark.asyncio
    @patch("models.user_models.get_connection")
    async def test_returns_zero_when_no_rows(self, mock_get_conn):
        """fetchone이 None을 반환하면 0을 반환한다."""
        cur_posts = _make_async_cursor(fetchone_result=None)
        cur_comments = _make_async_cursor(fetchone_result=None)
        cur_likes = _make_async_cursor(fetchone_result=None)

        conn = _make_async_conn([cur_posts, cur_comments, cur_likes])
        mock_get_conn.return_value = conn

        result = await get_user_stats(user_id=999)

        assert result == {
            "posts_count": 0,
            "comments_count": 0,
            "likes_received_count": 0,
        }
