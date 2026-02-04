"""common: 공통 응답 Pydantic 모델 모듈.

API 응답 및 공통 데이터 모델을 정의합니다.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


def create_response(
    code: str,
    message: str,
    data: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """표준 API 응답 딕셔너리를 생성합니다.

    Args:
        code: 응답 코드 (예: "SUCCESS", "POST_CREATED").
        message: 사용자에게 표시할 메시지.
        data: 응답 데이터 (기본값: 빈 딕셔너리).
        timestamp: 타임스탬프 (기본값: 현재 시간).

    Returns:
        표준 형식의 응답 딕셔너리.
    """
    return {
        "code": code,
        "message": message,
        "data": data if data is not None else {},
        "errors": [],
        "timestamp": timestamp or datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


class APIResponse(BaseModel):
    """표준 API 응답 모델.

    Attributes:
        code: 응답 코드.
        message: 응답 메시지.
        data: 응답 데이터.
        errors: 에러 목록.
        timestamp: 응답 타임스탬프.
    """

    code: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    )


class UserData(BaseModel):
    """사용자 정보 응답 모델.

    Attributes:
        user_id: 사용자 ID.
        email: 이메일 주소.
        nickname: 닉네임.
        profileImageUrl: 프로필 이미지 URL.
    """

    user_id: int
    email: str
    nickname: str
    profileImageUrl: str


def serialize_user(user) -> dict[str, Any]:
    """User 객체를 API 응답용 딕셔너리로 변환합니다.

    Args:
        user: User 데이터 객체 (id, email, nickname, profileImageUrl 속성 필요).

    Returns:
        사용자 정보 딕셔너리.
    """
    return {
        "user_id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "profileImageUrl": user.profileImageUrl,
    }
