"""Posts 도메인 -- 게시글 구독 테스트."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_test_post, create_verified_user


@pytest.mark.asyncio
async def test_subscribe_to_post(client: AsyncClient, fake, db):
    """PUT watching 후 GET으로 watching 상태를 확인한다."""
    # Arrange
    user = await create_verified_user(client, fake)
    post = await create_test_post(client, user["headers"])
    post_id = post["post_id"]

    # Act — watching으로 구독
    put_res = await client.put(
        f"/v1/posts/{post_id}/subscription",
        json={"level": "watching"},
        headers=user["headers"],
    )
    assert put_res.status_code == 200
    assert put_res.json()["level"] == "watching"

    # Assert — GET으로 확인
    get_res = await client.get(
        f"/v1/posts/{post_id}/subscription",
        headers=user["headers"],
    )
    assert get_res.status_code == 200
    assert get_res.json()["level"] == "watching"


@pytest.mark.asyncio
async def test_unsubscribe_from_post(client: AsyncClient, fake, db):
    """PUT watching → DELETE → GET으로 normal 상태를 확인한다."""
    # Arrange
    user = await create_verified_user(client, fake)
    post = await create_test_post(client, user["headers"])
    post_id = post["post_id"]

    # watching으로 구독
    put_res = await client.put(
        f"/v1/posts/{post_id}/subscription",
        json={"level": "watching"},
        headers=user["headers"],
    )
    assert put_res.status_code == 200

    # Act — 구독 해제
    del_res = await client.delete(
        f"/v1/posts/{post_id}/subscription",
        headers=user["headers"],
    )
    assert del_res.status_code == 200
    assert del_res.json()["level"] == "normal"

    # Assert — GET으로 normal 확인
    get_res = await client.get(
        f"/v1/posts/{post_id}/subscription",
        headers=user["headers"],
    )
    assert get_res.status_code == 200
    assert get_res.json()["level"] == "normal"


@pytest.mark.asyncio
async def test_mute_post(client: AsyncClient, fake, db):
    """PUT muted 후 GET으로 muted 상태를 확인한다."""
    # Arrange
    user = await create_verified_user(client, fake)
    post = await create_test_post(client, user["headers"])
    post_id = post["post_id"]

    # Act — muted로 구독
    put_res = await client.put(
        f"/v1/posts/{post_id}/subscription",
        json={"level": "muted"},
        headers=user["headers"],
    )
    assert put_res.status_code == 200
    assert put_res.json()["level"] == "muted"

    # Assert — GET으로 확인
    get_res = await client.get(
        f"/v1/posts/{post_id}/subscription",
        headers=user["headers"],
    )
    assert get_res.status_code == 200
    assert get_res.json()["level"] == "muted"


@pytest.mark.asyncio
async def test_default_subscription_is_normal(client: AsyncClient, fake, db):
    """구독하지 않은 상태에서 GET은 normal을 반환한다."""
    # Arrange
    user = await create_verified_user(client, fake)
    post = await create_test_post(client, user["headers"])
    post_id = post["post_id"]

    # Act
    get_res = await client.get(
        f"/v1/posts/{post_id}/subscription",
        headers=user["headers"],
    )

    # Assert
    assert get_res.status_code == 200
    assert get_res.json()["level"] == "normal"


@pytest.mark.asyncio
async def test_subscription_requires_auth(client: AsyncClient, fake, db):
    """미인증 사용자의 구독 조회 시 401을 반환한다."""
    # Arrange
    user = await create_verified_user(client, fake)
    post = await create_test_post(client, user["headers"])
    post_id = post["post_id"]

    # Act — 인증 헤더 없이 요청
    get_res = await client.get(f"/v1/posts/{post_id}/subscription")

    # Assert
    assert get_res.status_code == 401
