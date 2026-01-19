# comment_schemas: 댓글 관련 Pydantic 모델

from pydantic import BaseModel, Field, field_validator


# 댓글 생성 요청
class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("댓글 내용은 최소 1자 이상이어야 합니다.")
        return v


# 댓글 수정 요청
class UpdateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("댓글 내용은 최소 1자 이상이어야 합니다.")
        return v
