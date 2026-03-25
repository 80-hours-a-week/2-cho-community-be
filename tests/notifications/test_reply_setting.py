"""Notifications 도메인 -- reply 알림 설정 테스트.

reply 알림 유형의 기본값 조회 및 토글 동작 검증.
"""

import pytest

from tests.conftest import create_verified_user


@pytest.mark.asyncio
async def test_reply_notification_setting_default(client, fake):
    """알림 설정 기본값에 reply: True가 포함된다."""
    user = await create_verified_user(client, fake)

    res = await client.get("/v1/notifications/settings", headers=user["headers"])
    assert res.status_code == 200

    settings = res.json()["data"]["settings"]
    assert "reply" in settings
    assert settings["reply"] is True


@pytest.mark.asyncio
async def test_reply_notification_setting_toggle(client, fake):
    """reply 알림 설정을 비활성화한 뒤 다시 조회하면 false가 반환된다."""
    user = await create_verified_user(client, fake)

    # Act -- reply 알림 비활성화
    patch_res = await client.patch(
        "/v1/notifications/settings",
        headers=user["headers"],
        json={"reply": False},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["settings"]["reply"] is False

    # Assert -- GET으로 재확인
    get_res = await client.get("/v1/notifications/settings", headers=user["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["data"]["settings"]["reply"] is False
