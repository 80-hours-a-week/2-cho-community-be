from fastapi import APIRouter, Request
from controllers import auth_controller


auth_router = APIRouter(prefix="/v1/auth")


@auth_router.get("/me")
async def get_my_info(request: Request):
    return await auth_controller.get_my_info(request)


@auth_router.post("/session")
async def login(request: Request):
    return await auth_controller.login(request)


@auth_router.delete("/session")
async def logout(request: Request):
    return await auth_controller.logout(request)
