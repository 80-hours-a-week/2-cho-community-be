# post_schemas: 게시글 관련 Pydantic 모델

from pydantic import BaseModel, Field, field_validator
from typing import List


# ============ 게시글 요청 스키마 ============


# 게시글 생성 요청
class CreatePostRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    content: str = Field(..., min_length=1, max_length=10000)
    image_urls: List[str] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("제목은 최소 3자 이상이어야 합니다.")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("내용은 최소 1자 이상이어야 합니다.")
        return v

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, v: List[str] | None) -> List[str] | None:
        if v is None:
            return None
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        for url in v:
            if not any(url.lower().endswith(ext) for ext in allowed_extensions):
                raise ValueError(
                    "이미지는 .jpg, .jpeg, .png, .gif, .webp 형식만 허용됩니다."
                )
        return v


# 게시글 수정 요청
class UpdatePostRequest(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=100)
    content: str | None = Field(None, min_length=1, max_length=10000)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if len(v) < 3:
            raise ValueError("제목은 최소 3자 이상이어야 합니다.")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if len(v) < 1:
            raise ValueError("내용은 최소 1자 이상이어야 합니다.")
        return v
