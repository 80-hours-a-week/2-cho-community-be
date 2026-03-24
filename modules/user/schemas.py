"""user_schemas: 사용자 관련 Pydantic 모델 모듈.

사용자 등록, 수정, 비밀번호 변경, 탈퇴 요청 스키마를 정의합니다.
Annotated + AfterValidator 패턴으로 검증 로직 재사용 (DRY).
"""

import re
from typing import Annotated, Literal, get_args

from pydantic import AfterValidator, BaseModel, EmailStr, Field, field_validator

from schemas._image_validators import validate_profile_image_url

# Literal 타입으로 허용 배포판을 정의 — Pydantic v2 네이티브 검증 활용
Distro = Literal[
    "ubuntu",
    "fedora",
    "arch",
    "debian",
    "mint",
    "opensuse",
    "rocky",
    "nixos",
    "gentoo",
    "other",
]

# 패턴-에러 쌍을 하나의 딕셔너리로 관리하여 중복 구조 제거
_FIELD_RULES: dict[str, tuple[re.Pattern[str], str]] = {
    "password": (
        re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$"),
        "비밀번호는 대문자, 소문자, 숫자, 특수문자(@, $, !, %, *, ?, &)를 포함하여 8자 이상 20자 이하여야 합니다.",
    ),
    "nickname": (
        re.compile(r"^[a-zA-Z0-9_]{3,10}$"),
        "닉네임은 3자 이상 10자 이하의 영문, 숫자, 언더바로 구성하여야 합니다.",
    ),
}


def _make_checker(rule_key: str):
    """_FIELD_RULES 키로 AfterValidator 콜백을 생성하는 팩토리."""
    pattern, error_msg = _FIELD_RULES[rule_key]

    def _checker(v: str) -> str:
        if not pattern.match(v):
            raise ValueError(error_msg)
        return v

    _checker.__qualname__ = f"_check_{rule_key}"
    return _checker


# 재사용 타입 — Field 제약 + AfterValidator를 한 곳에서 정의
Password = Annotated[str, Field(min_length=8, max_length=20), AfterValidator(_make_checker("password"))]
Nickname = Annotated[str, Field(min_length=3, max_length=10), AfterValidator(_make_checker("nickname"))]


class CreateUserRequest(BaseModel):
    """사용자 등록 요청 모델.

    Attributes:
        email: 이메일 주소.
        password: 비밀번호 (8~20자, 대/소문자/숫자/특수문자 포함).
        nickname: 닉네임 (3~10자, 영문/숫자/언더바).
        profileImageUrl: 프로필 이미지 URL.
        terms_agreed: 이용약관 동의 여부.
    """

    email: EmailStr
    password: Password
    nickname: Nickname
    profileImageUrl: str | None = "/assets/profiles/default_profile.jpg"
    terms_agreed: bool

    @field_validator("terms_agreed")
    @classmethod
    def must_agree_terms(cls, v: bool) -> bool:
        """이용약관 동의 여부를 검증합니다."""
        if not v:
            raise ValueError("서비스 이용을 위해 이용약관에 동의해야 합니다.")
        return v

    @field_validator("profileImageUrl")
    @classmethod
    def validate_profile_image(cls, v: str | None) -> str:
        """프로필 이미지 URL 형식을 검증합니다."""
        if v is None:
            return "/assets/profiles/default_profile.jpg"
        result = validate_profile_image_url(v)
        return result if result is not None else "/assets/profiles/default_profile.jpg"


class UpdateUserRequest(BaseModel):
    """사용자 정보 수정 요청 모델.

    Attributes:
        nickname: 새 닉네임 (선택).
        profileImageUrl: 새 프로필 이미지 URL (선택) - 문자열 또는 {"url": "..."} 객체.
        distro: 배포판 (선택).
    """

    nickname: Nickname | None = None
    profileImageUrl: str | dict | None = None
    distro: Distro | Literal[""] | None = None

    @field_validator("distro")
    @classmethod
    def validate_distro(cls, v: str | None) -> str | None:
        """배포판 해제(빈 문자열) 허용 + Literal 범위 외 값 거부."""
        if v is None:
            return None
        if v == "":
            return ""
        if v not in get_args(Distro):
            raise ValueError(f"유효하지 않은 배포판입니다. 허용: {', '.join(sorted(get_args(Distro)))}")
        return v

    @field_validator("profileImageUrl", mode="before")
    @classmethod
    def validate_profile_image_url(cls, v: str | dict | None) -> str | None:
        """프로필 이미지 URL을 추출하고 보안 검증합니다."""
        return validate_profile_image_url(v)


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청 모델.

    Attributes:
        current_password: 현재 비밀번호 (본인 확인용).
        new_password: 새 비밀번호.
        new_password_confirm: 새 비밀번호 확인.
    """

    current_password: str
    new_password: Password
    new_password_confirm: str


class WithdrawRequest(BaseModel):
    """사용자 탈퇴 요청 모델.

    Attributes:
        password: 현재 비밀번호 (소셜 전용 계정은 None 허용).
        agree: 탈퇴 동의 여부.
    """

    password: str | None = None
    agree: bool

    @field_validator("agree")
    @classmethod
    def must_agree(cls, v: bool) -> bool:
        """탈퇴 동의 여부를 검증합니다."""
        if not v:
            raise ValueError("계정을 삭제하기 전에 반드시 동의하여야 합니다.")
        return v
