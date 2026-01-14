from fastapi import APIRouter, Request, status
from controllers import auth_controller

# 라우터 생성
auth_router = APIRouter(prefix="/v1/auth", tags=["auth"])


# 로그인
@auth_router.post("/session", status_code=status.HTTP_200_OK)
async def login(request: Request):
    return await auth_controller.login(request)


# 로그아웃
@auth_router.delete("/session", status_code=status.HTTP_200_OK)
async def logout(request: Request):
    return await auth_controller.logout(request)


# 로그인 상태 검증하기
@auth_router.get("/me", status_code=status.HTTP_200_OK)
async def get_my_info(request: Request):
    return await auth_controller.get_my_info(request)
