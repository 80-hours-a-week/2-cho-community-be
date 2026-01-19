# post_router: 게시글, 댓글, 좋아요 관련 라우터

from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, status
from controllers import post_controller
from dependencies.auth import get_current_user
from models.user_models import User
from schemas.post_schemas import CreatePostRequest, UpdatePostRequest
from schemas.comment_schemas import CreateCommentRequest, UpdateCommentRequest


# 라우터 생성
post_router = APIRouter(prefix="/v1/posts", tags=["posts"])


# ============ 게시글 라우터 ============


# 게시글 목록 조회 (페이지네이션, 최신순)
@post_router.get("/", status_code=status.HTTP_200_OK)
async def get_posts(
    request: Request,
    page: int = Query(0, ge=0, description="페이지 번호 (0부터 시작)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 게시글 수"),
):
    return await post_controller.get_posts(page, limit, request)


# 특정 게시글 상세 조회
@post_router.get("/{post_id}", status_code=status.HTTP_200_OK)
async def get_post(post_id: int, request: Request):
    return await post_controller.get_post(post_id, request)


# 게시글 생성
@post_router.post("", status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: CreatePostRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return await post_controller.create_post(post_data, current_user, request)


# 게시글 수정
@post_router.patch("/{post_id}", status_code=status.HTTP_200_OK)
async def update_post(
    post_id: int,
    post_data: UpdatePostRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return await post_controller.update_post(post_id, post_data, current_user, request)


# 게시글 삭제
@post_router.delete("/{post_id}", status_code=status.HTTP_200_OK)
async def delete_post(
    post_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return await post_controller.delete_post(post_id, current_user, request)


# 이미지 업로드
@post_router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    return await post_controller.upload_image(file, current_user, request)


# ============ 좋아요 라우터 ============


# 게시글 좋아요 추가
@post_router.post("/{post_id}/likes", status_code=status.HTTP_201_CREATED)
async def like_post(
    post_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return await post_controller.like_post(post_id, current_user, request)


# 게시글 좋아요 취소
@post_router.delete("/{post_id}/likes", status_code=status.HTTP_200_OK)
async def unlike_post(
    post_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return await post_controller.unlike_post(post_id, current_user, request)


# ============ 댓글 라우터 ============


# 댓글 생성
@post_router.post("/{post_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    comment_data: CreateCommentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return await post_controller.create_comment(
        post_id, comment_data, current_user, request
    )


# 댓글 수정
@post_router.put("/{post_id}/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def update_comment(
    post_id: int,
    comment_id: int,
    comment_data: UpdateCommentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return await post_controller.update_comment(
        post_id, comment_id, comment_data, current_user, request
    )


# 댓글 삭제
@post_router.delete("/{post_id}/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comment(
    post_id: int,
    comment_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return await post_controller.delete_comment(
        post_id, comment_id, current_user, request
    )
