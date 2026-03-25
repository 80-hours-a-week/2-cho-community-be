"""다이제스트 이메일 데이터 쿼리 + 엔드포인트 테스트."""

import pytest

from core.database.connection import get_connection
from tests.conftest import create_admin_user, create_test_post, create_verified_user


@pytest.mark.asyncio
async def test_get_eligible_users(client, fake, db):
    """비활성 사용자만 다이제스트 수신 대상."""
    from modules.notification.digest_models import get_eligible_users

    user = await create_verified_user(client, fake)
    eligible = await get_eligible_users("weekly", lookback_days=7)
    user_ids = [u["id"] for u in eligible]
    assert user["user_id"] in user_ids


@pytest.mark.asyncio
async def test_active_user_excluded(client, fake, db):
    """활성 사용자는 제외."""
    from modules.notification.digest_models import get_eligible_users

    user = await create_verified_user(client, fake)
    post = await create_test_post(client, user["headers"])
    # DB에 직접 view log 삽입 (GET 요청은 follow_redirects 이슈 가능)
    async with get_connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO post_view_log (user_id, post_id) VALUES (%s, %s)",
            (user["user_id"], post["post_id"]),
        )
    eligible = await get_eligible_users("weekly", lookback_days=7)
    user_ids = [u["id"] for u in eligible]
    assert user["user_id"] not in user_ids


@pytest.mark.asyncio
async def test_get_top_posts(client, fake, db):
    """인기 게시글 조회."""
    from modules.notification.digest_models import get_top_posts

    user = await create_verified_user(client, fake)
    await create_test_post(client, user["headers"])
    top = await get_top_posts(lookback_days=7, limit=5)
    assert len(top) >= 1
    # 반환 형식 검증
    assert "id" in top[0]
    assert "title" in top[0]
    assert "likes" in top[0]
    assert "comments" in top[0]


@pytest.mark.asyncio
async def test_get_following_posts(client, fake, db):
    """팔로잉 사용자의 게시글 조회."""
    from modules.notification.digest_models import get_following_posts

    user_a = await create_verified_user(client, fake)
    user_b = await create_verified_user(client, fake)

    # user_a가 user_b를 팔로우
    await client.post(
        f"/v1/users/{user_b['user_id']}/follow",
        headers=user_a["headers"],
    )
    # user_b가 게시글 작성
    await create_test_post(client, user_b["headers"])

    posts = await get_following_posts(user_a["user_id"], lookback_days=7, limit=3)
    assert len(posts) >= 1
    assert "nickname" in posts[0]


@pytest.mark.asyncio
async def test_get_unread_notification_count(client, fake, db):
    """읽지 않은 알림 수 조회."""
    from modules.notification.digest_models import get_unread_notification_count

    user = await create_verified_user(client, fake)
    count = await get_unread_notification_count(user["user_id"])
    assert count == 0


@pytest.mark.asyncio
async def test_digest_endpoint_requires_auth(client, fake, db):
    """다이제스트 엔드포인트는 인증 필요."""
    res = await client.post("/v1/admin/digest/send")
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_digest_endpoint_admin_access(client, fake, db):
    """관리자는 다이제스트 엔드포인트 접근 가능."""
    admin = await create_admin_user(client, fake)
    res = await client.post("/v1/admin/digest/send", headers=admin["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "daily" in data["data"]
    assert "weekly" in data["data"]
    assert "errors" in data["data"]
