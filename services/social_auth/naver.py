"""네이버 OAuth 2.0 프로바이더."""

import httpx

from core.config import settings
from services.social_auth.base import SocialUserInfo

NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_USER_URL = "https://openapi.naver.com/v1/nid/me"


class NaverProvider:
    """네이버 소셜 로그인 제공자."""

    provider_name = "naver"

    def get_authorize_url(self, state: str) -> str:
        """네이버 인증 페이지 URL을 생성합니다."""
        params = {
            "client_id": settings.NAVER_CLIENT_ID,
            "redirect_uri": settings.NAVER_REDIRECT_URI,
            "response_type": "code",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{NAVER_AUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> str:
        """authorization code → access_token 교환."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                NAVER_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.NAVER_CLIENT_ID,
                    "client_secret": settings.NAVER_CLIENT_SECRET,
                    "code": code,
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def get_user_info(self, access_token: str) -> SocialUserInfo:
        """access_token → 사용자 정보 조회."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                NAVER_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json().get("response", {})

        return SocialUserInfo(
            provider="naver",
            provider_id=str(data.get("id", "")),
            email=data.get("email"),
            # 네이버는 이메일 제공 시 인증된 것으로 간주
            email_verified=bool(data.get("email")),
            profile_image=data.get("profile_image"),
        )
