from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from routers import user_router, auth_router

app = FastAPI()

# 메인 어플리케이션에 라우터 포함
app.include_router(user_router, tags=["users"])
app.include_router(auth_router, tags=["auth"])

# SessionMiddleware: 모든 요청과 응답에서 세션을 처리.
app.add_middleware(
    SessionMiddleware,
    secret_key="secret-key-proto",
    max_age=24 * 60 * 60,
    same_site="lax",
    https_only=False,
)

# 허용된 origin 목록
origins = [
    "http://localhost",
    "http://localhost:8000",
]

# CORSMiddleware 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
