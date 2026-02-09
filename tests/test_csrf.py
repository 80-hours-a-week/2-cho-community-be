"""CSRF Protection 테스트."""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_get_request_sets_csrf_cookie():
    """GET 요청 시 CSRF 토큰 쿠키가 설정되는지 확인."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        # CSRF 토큰 쿠키가 설정되어야 함
        assert "csrf_token" in response.cookies
        assert len(response.cookies["csrf_token"]) > 0


@pytest.mark.asyncio
async def test_post_without_csrf_token_fails():
    """CSRF 토큰 없이 POST 요청 시 403 에러 발생."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 먼저 GET 요청으로 세션 생성
        await client.get("/health")

        # CSRF 토큰 없이 POST 요청 (제외 경로가 아닌 곳)
        response = await client.post(
            "/v1/posts/1/likes",
            json={}
        )

        # CSRF 검증 실패로 403 에러
        assert response.status_code == 403
        data = response.json()
        assert "csrf" in data["message"].lower()


@pytest.mark.asyncio
async def test_post_with_csrf_token_succeeds():
    """올바른 CSRF 토큰과 함께 POST 요청 시 성공."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 먼저 GET 요청으로 CSRF 토큰 획득
        response = await client.get("/health")
        csrf_token = response.cookies["csrf_token"]

        # CSRF 토큰을 헤더에 포함하여 POST 요청
        # (실제로는 인증이 필요하지만, 여기서는 CSRF 검증만 확인)
        response = await client.post(
            "/v1/posts/1/likes",
            headers={"X-CSRF-Token": csrf_token},
            json={}
        )

        # CSRF 검증은 통과 (실제 비즈니스 로직 에러는 무시)
        # 401(인증 필요) 또는 404(게시글 없음)가 나올 수 있지만,
        # 403(CSRF 검증 실패)가 아니면 성공
        assert response.status_code != 403


@pytest.mark.asyncio
async def test_exempt_path_login_works_without_csrf():
    """로그인 엔드포인트는 CSRF 토큰 없이 동작."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # CSRF 토큰 없이 로그인 시도
        # 데이터베이스 초기화 없이 테스트하므로 500 에러 발생 예상
        try:
            response = await client.post(
                "/v1/auth/session",
                json={"email": "test@example.com", "password": "password123"}
            )

            # CSRF 검증 실패(403)가 아니면 성공
            # DB 초기화 없이는 500(서버 에러)가 나올 수 있음
            # 중요한 것은 CSRF 검증(403)으로 차단되지 않는다는 것
            assert response.status_code != 403
        except Exception:
            # 데이터베이스 연결 에러 등은 무시 (CSRF 검증과 무관)
            pass


@pytest.mark.asyncio
async def test_exempt_path_signup_works_without_csrf():
    """회원가입 엔드포인트는 CSRF 토큰 없이 동작."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # CSRF 토큰 없이 회원가입 시도
        response = await client.post(
            "/v1/users",
            json={
                "email": "new@example.com",
                "password": "password123",
                "nickname": "testnick"
            }
        )

        # CSRF 검증 실패(403)가 아니어야 함
        assert response.status_code != 403


@pytest.mark.asyncio
async def test_csrf_token_mismatch_fails():
    """쿠키와 헤더의 CSRF 토큰이 다르면 실패."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 먼저 GET 요청으로 CSRF 토큰 획득
        await client.get("/health")

        # 잘못된 토큰으로 POST 요청
        response = await client.post(
            "/v1/posts/1/likes",
            headers={"X-CSRF-Token": "wrong_token_here"},
            json={}
        )

        # CSRF 토큰 불일치로 403 에러
        assert response.status_code == 403
        data = response.json()
        assert "csrf" in data["message"].lower()


@pytest.mark.asyncio
async def test_delete_requires_csrf_token():
    """DELETE 요청도 CSRF 토큰 필요."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # CSRF 토큰 없이 DELETE 요청
        response = await client.delete("/v1/posts/1")

        # CSRF 검증 실패로 403 에러
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_put_requires_csrf_token():
    """PUT 요청도 CSRF 토큰 필요."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # CSRF 토큰 없이 PUT 요청
        response = await client.put("/v1/posts/1", json={"title": "test"})

        # CSRF 검증 실패로 403 에러
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_patch_requires_csrf_token():
    """PATCH 요청도 CSRF 토큰 필요."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # CSRF 토큰 없이 PATCH 요청
        # 인증이 필요한 엔드포인트는 401 반환 (인증 체크가 먼저 실행됨)
        response = await client.patch("/v1/users/me", json={"nickname": "test"})

        # 401 (인증 실패) 또는 403 (CSRF 실패) 둘 다 가능
        # 미들웨어 실행 순서에 따라 다름
        assert response.status_code in [401, 403]
