"""email_templates: 이메일 HTML/텍스트 템플릿 빌더.

Camp Linux 브랜딩 기반의 다이제스트 이메일 생성 유틸리티.
HTML 템플릿은 인라인 CSS를 사용하여 다양한 이메일 클라이언트와의 호환성을 보장합니다.
"""


def build_digest_html(
    top_posts: list[dict],
    following_posts: list[dict],
    unread_count: int,
    subscription_updates: int,
    site_url: str,
) -> str:
    """HTML 다이제스트 이메일 본문 생성.

    Args:
        top_posts: 인기 게시글 목록. 각 항목은 {id, title, likes, comments} 형태.
        following_posts: 팔로잉 활동 목록. 각 항목은 {id, title, nickname} 형태.
        unread_count: 읽지 않은 알림 수.
        subscription_updates: 구독 업데이트 수.
        site_url: 사이트 기본 URL (예: https://my-community.shop).

    Returns:
        완성된 HTML 이메일 본문 문자열.
    """
    # 인기 게시글 섹션 HTML 생성
    top_posts_html = _build_top_posts_html(top_posts, site_url)

    # 팔로잉 활동 섹션 HTML 생성
    following_html = _build_following_html(following_posts, site_url)

    # 알림/구독 요약 섹션 HTML 생성
    summary_html = _build_summary_html(unread_count, subscription_updates)

    notifications_url = f"{site_url}/notifications"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Camp Linux 주간 다이제스트</title>
</head>
<body style="margin:0;padding:0;background-color:#0f0f1a;font-family:'Courier New',Courier,monospace;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#0f0f1a;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%;background-color:#1a1a2e;border-radius:8px;
                      border:1px solid #2a2a4e;overflow:hidden;">

          <!-- 헤더 -->
          <tr>
            <td style="background-color:#1a1a2e;padding:32px 40px;border-bottom:2px solid #e67e22;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td>
                    <span style="color:#e67e22;font-size:22px;font-weight:bold;
                                 letter-spacing:2px;">$ Camp Linux</span>
                    <br>
                    <span style="color:#8888aa;font-size:13px;margin-top:4px;display:block;">
                      주간 커뮤니티 다이제스트
                    </span>
                  </td>
                  <td align="right">
                    <span style="color:#4a4a6a;font-size:11px;">
                      weekly digest
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- 본문 -->
          <tr>
            <td style="padding:32px 40px;">

              {top_posts_html}

              {following_html}

              {summary_html}

              <!-- CTA 버튼 -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="margin-top:32px;">
                <tr>
                  <td align="center">
                    <a href="{site_url}"
                       style="display:inline-block;background-color:#e67e22;color:#ffffff;
                              text-decoration:none;padding:14px 36px;border-radius:4px;
                              font-size:14px;font-weight:bold;letter-spacing:1px;">
                      커뮤니티 방문하기 &gt;
                    </a>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- 푸터 -->
          <tr>
            <td style="background-color:#12122a;padding:20px 40px;
                       border-top:1px solid #2a2a4e;text-align:center;">
              <p style="margin:0;color:#4a4a6a;font-size:11px;line-height:1.6;">
                Camp Linux — 리눅스 커뮤니티<br>
                <a href="{notifications_url}"
                   style="color:#6666aa;text-decoration:underline;">
                  알림 설정 / 구독 해지
                </a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _build_top_posts_html(top_posts: list[dict], site_url: str) -> str:
    """인기 게시글 섹션 HTML 조각을 생성합니다."""
    if not top_posts:
        items_html = '<p style="color:#4a4a6a;font-size:13px;margin:8px 0;">이번 주 인기 게시글이 없습니다.</p>'
    else:
        rows = []
        for post in top_posts:
            post_url = f"{site_url}/detail?id={post['id']}"
            title = post.get("title", "")
            likes = post.get("likes", 0)
            comments = post.get("comments", 0)
            rows.append(
                f"<tr>"
                f'<td style="padding:10px 0;border-bottom:1px solid #2a2a4e;">'
                f'<a href="{post_url}" style="color:#e67e22;text-decoration:none;'
                f'font-size:14px;font-weight:bold;">{title}</a>'
                f"<br>"
                f'<span style="color:#6666aa;font-size:12px;">'
                f"좋아요 {likes} &nbsp;|&nbsp; 댓글 {comments}"
                f"</span>"
                f"</td>"
                f"</tr>"
            )
        items_html = f'<table width="100%" cellpadding="0" cellspacing="0" border="0">{"".join(rows)}</table>'

    return f"""
      <div style="margin-bottom:28px;">
        <h2 style="color:#e67e22;font-size:14px;letter-spacing:2px;
                   margin:0 0 12px 0;padding-bottom:8px;
                   border-bottom:1px solid #2a2a4e;">
          &gt; 인기 게시글
        </h2>
        {items_html}
      </div>"""


def _build_following_html(following_posts: list[dict], site_url: str) -> str:
    """팔로잉 활동 섹션 HTML 조각을 생성합니다."""
    if not following_posts:
        items_html = '<p style="color:#4a4a6a;font-size:13px;margin:8px 0;">팔로잉한 사용자의 새 게시글이 없습니다.</p>'
    else:
        rows = []
        for post in following_posts:
            post_url = f"{site_url}/detail?id={post['id']}"
            title = post.get("title", "")
            nickname = post.get("nickname", "")
            rows.append(
                f"<tr>"
                f'<td style="padding:10px 0;border-bottom:1px solid #2a2a4e;">'
                f'<a href="{post_url}" style="color:#aaaadd;text-decoration:none;font-size:14px;">'
                f"{title}</a>"
                f"<br>"
                f'<span style="color:#6666aa;font-size:12px;">by {nickname}</span>'
                f"</td>"
                f"</tr>"
            )
        items_html = f'<table width="100%" cellpadding="0" cellspacing="0" border="0">{"".join(rows)}</table>'

    return f"""
      <div style="margin-bottom:28px;">
        <h2 style="color:#e67e22;font-size:14px;letter-spacing:2px;
                   margin:0 0 12px 0;padding-bottom:8px;
                   border-bottom:1px solid #2a2a4e;">
          &gt; 팔로잉 활동
        </h2>
        {items_html}
      </div>"""


def _build_summary_html(unread_count: int, subscription_updates: int) -> str:
    """알림/구독 요약 섹션 HTML 조각을 생성합니다."""
    return f"""
      <div style="background-color:#12122a;border-radius:4px;padding:16px 20px;
                  border-left:3px solid #e67e22;margin-bottom:8px;">
        <h2 style="color:#e67e22;font-size:14px;letter-spacing:2px;margin:0 0 12px 0;">
          &gt; 요약
        </h2>
        <table cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="color:#8888aa;font-size:13px;padding:3px 0;padding-right:16px;">
              읽지 않은 알림
            </td>
            <td style="color:#e67e22;font-size:13px;font-weight:bold;padding:3px 0;">
              {unread_count}개
            </td>
          </tr>
          <tr>
            <td style="color:#8888aa;font-size:13px;padding:3px 0;padding-right:16px;">
              구독 업데이트
            </td>
            <td style="color:#e67e22;font-size:13px;font-weight:bold;padding:3px 0;">
              {subscription_updates}개
            </td>
          </tr>
        </table>
      </div>"""


def build_digest_text(
    top_posts: list[dict],
    following_posts: list[dict],
    unread_count: int,
    subscription_updates: int,
    site_url: str,
) -> str:
    """텍스트 다이제스트 이메일 본문 생성 (HTML 미지원 클라이언트 폴백).

    Args:
        top_posts: 인기 게시글 목록. 각 항목은 {id, title, likes, comments} 형태.
        following_posts: 팔로잉 활동 목록. 각 항목은 {id, title, nickname} 형태.
        unread_count: 읽지 않은 알림 수.
        subscription_updates: 구독 업데이트 수.
        site_url: 사이트 기본 URL (예: https://my-community.shop).

    Returns:
        완성된 텍스트 이메일 본문 문자열.
    """
    lines = [
        "=" * 50,
        "  Camp Linux — 주간 커뮤니티 다이제스트",
        "=" * 50,
        "",
    ]

    # 인기 게시글
    lines.append("[ 인기 게시글 ]")
    lines.append("-" * 30)
    if top_posts:
        for i, post in enumerate(top_posts, 1):
            title = post.get("title", "")
            likes = post.get("likes", 0)
            comments = post.get("comments", 0)
            post_url = f"{site_url}/detail?id={post['id']}"
            lines.append(f"{i}. {title}")
            lines.append(f"   좋아요 {likes}  |  댓글 {comments}")
            lines.append(f"   {post_url}")
    else:
        lines.append("이번 주 인기 게시글이 없습니다.")
    lines.append("")

    # 팔로잉 활동
    lines.append("[ 팔로잉 활동 ]")
    lines.append("-" * 30)
    if following_posts:
        for post in following_posts:
            title = post.get("title", "")
            nickname = post.get("nickname", "")
            post_url = f"{site_url}/detail?id={post['id']}"
            lines.append(f"- {title}  (by {nickname})")
            lines.append(f"  {post_url}")
    else:
        lines.append("팔로잉한 사용자의 새 게시글이 없습니다.")
    lines.append("")

    # 요약
    lines.append("[ 요약 ]")
    lines.append("-" * 30)
    lines.append(f"읽지 않은 알림: {unread_count}개")
    lines.append(f"구독 업데이트:  {subscription_updates}개")
    lines.append("")

    # CTA 및 푸터
    lines.append("=" * 50)
    lines.append(f"커뮤니티 방문: {site_url}")
    lines.append(f"알림 설정 / 구독 해지: {site_url}/notifications")
    lines.append("=" * 50)

    return "\n".join(lines)
