"""소셜 프로바이더 팩토리."""

from fastapi import HTTPException, status

from services.social_auth.kakao import KakaoProvider
from services.social_auth.naver import NaverProvider

_PROVIDERS = {
    "kakao": KakaoProvider,
    "naver": NaverProvider,
}

SUPPORTED_PROVIDERS = set(_PROVIDERS.keys())


def get_provider(name: str) -> KakaoProvider | NaverProvider:
    """프로바이더 이름으로 구현체를 생성합니다."""
    cls = _PROVIDERS.get(name)
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "unsupported_provider",
                "message": f"지원하지 않는 소셜 로그인: {name}",
            },
        )
    return cls()
