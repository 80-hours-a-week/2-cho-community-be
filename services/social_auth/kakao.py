"""카카오 OAuth 2.0 프로바이더."""

import httpx

from core.config import settings
from services.social_auth.base import SocialUserInfo

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"


class KakaoProvider:
    """카카오 소셜 로그인 제공자."""

    provider_name = "kakao"

    def get_authorize_url(self, state: str) -> str:
        """카카오 인증 페이지 URL을 생성합니다."""
        params = {
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "response_type": "code",
            "state": state,
            "scope": "account_email profile_image",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{KAKAO_AUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> str:
        """authorization code → access_token 교환."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                KAKAO_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.KAKAO_CLIENT_ID,
                    "client_secret": settings.KAKAO_CLIENT_SECRET,
                    "redirect_uri": settings.KAKAO_REDIRECT_URI,
                    "code": code,
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def get_user_info(self, access_token: str) -> SocialUserInfo:
        """access_token → 사용자 정보 조회."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                KAKAO_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()

        kakao_account = data.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        return SocialUserInfo(
            provider="kakao",
            provider_id=str(data["id"]),
            email=kakao_account.get("email"),
            email_verified=kakao_account.get("is_email_verified", False),
            profile_image=profile.get("profile_image_url"),
        )
