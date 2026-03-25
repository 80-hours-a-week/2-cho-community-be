"""subscription_schemas: 게시글 구독 요청/응답 스키마."""

from typing import Literal

from pydantic import BaseModel


class SubscriptionRequest(BaseModel):
    """구독 수준 변경 요청."""

    level: Literal["watching", "muted"]


class SubscriptionResponse(BaseModel):
    """구독 수준 응답."""

    post_id: int
    level: Literal["watching", "normal", "muted"]
