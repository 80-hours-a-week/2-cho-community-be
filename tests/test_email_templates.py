"""test_email_templates: 이메일 다이제스트 템플릿 빌더 단위 테스트."""

from core.utils.email_templates import build_digest_html, build_digest_text


def test_build_digest_html() -> None:
    html = build_digest_html(
        top_posts=[{"title": "리눅스 커널 6.x", "likes": 12, "comments": 5, "id": 1}],
        following_posts=[{"title": "Arch 설치 가이드", "nickname": "tux", "id": 2}],
        unread_count=4,
        subscription_updates=7,
        site_url="https://my-community.shop",
    )
    assert "<html" in html.lower()
    assert "리눅스 커널 6.x" in html
    assert "Arch 설치 가이드" in html
    assert "https://my-community.shop" in html


def test_build_digest_text() -> None:
    text = build_digest_text(
        top_posts=[{"title": "리눅스 커널 6.x", "likes": 12, "comments": 5, "id": 1}],
        following_posts=[],
        unread_count=0,
        subscription_updates=0,
        site_url="https://my-community.shop",
    )
    assert "리눅스 커널 6.x" in text
    assert "Camp Linux" in text


def test_build_digest_html_empty() -> None:
    """콘텐츠가 없어도 에러 없이 HTML 생성."""
    html = build_digest_html(
        top_posts=[],
        following_posts=[],
        unread_count=0,
        subscription_updates=0,
        site_url="https://example.com",
    )
    assert "<html" in html.lower()


def test_build_digest_html_post_links() -> None:
    """게시글 링크가 올바른 URL 형식으로 생성되는지 확인."""
    html = build_digest_html(
        top_posts=[{"title": "테스트 포스트", "likes": 3, "comments": 1, "id": 42}],
        following_posts=[{"title": "팔로잉 포스트", "nickname": "user1", "id": 99}],
        unread_count=1,
        subscription_updates=2,
        site_url="https://my-community.shop",
    )
    assert "detail?id=42" in html
    assert "detail?id=99" in html


def test_build_digest_text_links() -> None:
    """텍스트 버전에 게시글 URL과 사이트 링크가 포함되는지 확인."""
    text = build_digest_text(
        top_posts=[{"title": "커널 빌드 팁", "likes": 5, "comments": 2, "id": 10}],
        following_posts=[{"title": "Vim 설정", "nickname": "admin", "id": 20}],
        unread_count=3,
        subscription_updates=1,
        site_url="https://my-community.shop",
    )
    assert "detail?id=10" in text
    assert "detail?id=20" in text
    assert "https://my-community.shop/notifications" in text


def test_build_digest_text_empty_posts() -> None:
    """팔로잉 목록이 비어있을 때 텍스트 생성이 정상 동작하는지 확인."""
    text = build_digest_text(
        top_posts=[],
        following_posts=[],
        unread_count=0,
        subscription_updates=0,
        site_url="https://example.com",
    )
    assert "Camp Linux" in text
    assert "이번 주 인기 게시글이 없습니다." in text
    assert "팔로잉한 사용자의 새 게시글이 없습니다." in text


def test_build_digest_html_summary_counts() -> None:
    """요약 섹션에 알림/구독 카운트가 올바르게 표시되는지 확인."""
    html = build_digest_html(
        top_posts=[],
        following_posts=[],
        unread_count=15,
        subscription_updates=3,
        site_url="https://my-community.shop",
    )
    assert "15개" in html
    assert "3개" in html


def test_build_digest_html_unsubscribe_link() -> None:
    """구독 해지 링크가 알림 설정 URL로 연결되는지 확인."""
    html = build_digest_html(
        top_posts=[],
        following_posts=[],
        unread_count=0,
        subscription_updates=0,
        site_url="https://my-community.shop",
    )
    assert "https://my-community.shop/notifications" in html
