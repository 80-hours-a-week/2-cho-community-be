# schemas: Pydantic 모델들이 정의된 패키지

from .post_schemas import (
    CreatePostRequest,
    UpdatePostRequest,
)

from .comment_schemas import (
    CreateCommentRequest,
    UpdateCommentRequest,
)

__all__ = [
    "CreatePostRequest",
    "UpdatePostRequest",
    "CreateCommentRequest",
    "UpdateCommentRequest",
]
