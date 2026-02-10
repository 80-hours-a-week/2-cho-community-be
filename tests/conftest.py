import sys
import os

# Rate Limiter 우회를 위한 테스트 환경 변수 설정
os.environ["TESTING"] = "true"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from database.connection import get_connection, init_db, close_db
from faker import Faker


class CSRFAsyncClient(AsyncClient):
    """CSRF 토큰을 자동으로 포함하는 AsyncClient 래퍼."""

    async def request(self, method, url, **kwargs):
        """요청 시 CSRF 토큰을 자동으로 헤더에 추가."""
        # POST, PUT, PATCH, DELETE 요청에만 CSRF 토큰 추가
        if method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
            # 쿠키에서 CSRF 토큰 가져오기
            csrf_token = self.cookies.get("csrf_token")
            if csrf_token:
                # 기존 헤더가 None이면 새 dict 생성
                headers = kwargs.get("headers")
                if headers is None:
                    headers = {}
                elif not isinstance(headers, dict):
                    # 다른 타입(예: list of tuples)이면 dict로 변환
                    headers = dict(headers)
                else:
                    # dict면 복사본 생성 (원본 수정 방지)
                    headers = dict(headers)

                headers["X-CSRF-Token"] = csrf_token
                kwargs["headers"] = headers

        return await super().request(method, url, **kwargs)


async def clear_all_data() -> None:
    """테스트용 헬퍼: 모든 게시글 관련 데이터를 삭제합니다."""
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            await cur.execute("TRUNCATE TABLE post_view_log")
            await cur.execute("TRUNCATE TABLE post_like")
            await cur.execute("TRUNCATE TABLE comment")
            await cur.execute("TRUNCATE TABLE post")
            await cur.execute("TRUNCATE TABLE user_session")
            await cur.execute("TRUNCATE TABLE user")
            await cur.execute("SET FOREIGN_KEY_CHECKS = 1")


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest_asyncio.fixture(scope="function")
async def db():
    """각 테스트 함수 실행 전 데이터 초기화 및 DB 연결 관리"""
    await init_db()
    try:
        await clear_all_data()
        yield
    finally:
        await close_db()


@pytest_asyncio.fixture
async def client(db):
    """API 테스트를 위한 CSRF 지원 Async Client"""
    transport = ASGITransport(app=app)
    async with CSRFAsyncClient(transport=transport, base_url="http://test") as ac:
        # GET 요청으로 CSRF 토큰 획득
        await ac.get("/health")
        yield ac


@pytest.fixture
def fake():
    return Faker("ko_KR")


@pytest.fixture
def user_payload(fake):
    """회원가입용 페이로드 생성"""
    return {
        "email": fake.email(),
        "password": "Password123!",
        # 닉네임 길이 5~10자 보장
        "nickname": fake.lexify(text="?????") + str(fake.random_int(10, 99)),
    }


@pytest_asyncio.fixture
async def authorized_user(client, user_payload):
    """회원가입 및 로그인이 완료된 클라이언트와 유저 정보 반환"""
    # 회원가입 (Form)
    signup_res = await client.post("/v1/users/", data=user_payload)

    if signup_res.status_code != 201:
        print(f"Signup failed: {signup_res.status_code}, {signup_res.text}")

    assert signup_res.status_code == 201

    # 로그인 (JSON)
    login_res = await client.post(
        "/v1/auth/session",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login_res.status_code == 200

    user_info = login_res.json()["data"]["user"]
    return client, user_info, user_payload
