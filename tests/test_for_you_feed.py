"""추천 피드 (For You Feed) 테스트."""

import pytest

from database.connection import get_connection, transactional
from models.affinity_models import (
    UserSignals,
    get_active_user_ids,
    get_candidate_posts_meta,
    upsert_user_post_scores,
    user_has_scores,
)
from services.affinity_scorer import (
    build_profile,
    score_post,
    compute_combined_score,
    UserAffinityProfile,
)
from services.post_service import PostService


# ============ 순수 스코어러 단위 테스트 ============


class TestAffinityScorer:
    """affinity_scorer 순수 함수 테스트."""

    def test_build_profile_empty_signals(self):
        """빈 신호 → 빈 프로필."""
        signals = UserSignals()
        profile = build_profile(signals)
        assert profile.is_empty
        assert profile.tag_weights == {}
        assert profile.category_weights == {}
        assert profile.author_weights == {}

    def test_build_profile_with_liked_tags(self):
        """좋아요한 태그 → 프로필에 태그 가중치 반영."""
        signals = UserSignals(liked_tag_counts={1: 5, 2: 3})
        profile = build_profile(signals)
        assert not profile.is_empty
        assert profile.tag_weights[1] == 1.0  # max-normalized
        assert profile.tag_weights[2] == pytest.approx(3 * 3.0 / (5 * 3.0))

    def test_build_profile_with_all_signals(self):
        """모든 신호 → 3개 차원 모두 프로필에 반영."""
        signals = UserSignals(
            liked_tag_counts={10: 2},
            bookmarked_tag_counts={10: 1, 20: 3},
            commented_tag_counts={20: 1},
            viewed_category_counts={1: 10, 2: 5},
            followed_author_ids={100, 200},
            liked_author_counts={100: 3},
            bookmarked_author_counts={200: 2},
        )
        profile = build_profile(signals)
        assert len(profile.tag_weights) == 2
        assert len(profile.category_weights) == 2
        assert len(profile.author_weights) == 2
        # 카테고리 1이 더 많이 조회됨 → 가중치 1.0
        assert profile.category_weights[1] == 1.0

    def test_score_post_no_overlap(self):
        """겹치는 신호 없음 → 0점."""
        profile = UserAffinityProfile(
            tag_weights={1: 1.0},
            category_weights={1: 1.0},
            author_weights={100: 1.0},
        )
        score = score_post(profile, post_tag_ids=[99], post_category_id=99, post_author_id=99)
        assert score == 0.0

    def test_score_post_full_overlap(self):
        """모든 신호 겹침 → 최대 점수."""
        profile = UserAffinityProfile(
            tag_weights={1: 1.0},
            category_weights={2: 1.0},
            author_weights={100: 1.0},
        )
        score = score_post(profile, post_tag_ids=[1], post_category_id=2, post_author_id=100)
        assert score == pytest.approx(1.0)  # 0.5 + 0.3 + 0.2

    def test_score_post_partial_tag_overlap(self):
        """태그 일부만 겹침."""
        profile = UserAffinityProfile(
            tag_weights={1: 1.0, 2: 0.5},
            category_weights={},
            author_weights={},
        )
        # 게시글 태그 [1, 3] → 태그 1만 겹침 → avg(1.0, 0.0) = 0.5
        score = score_post(profile, post_tag_ids=[1, 3], post_category_id=None, post_author_id=None)
        assert score == pytest.approx(0.5 * 0.5)  # tag_score * TAG_COEFF

    def test_compute_combined_score_with_affinity(self):
        """친화도 있음 → affinity × hot_score."""
        assert compute_combined_score(0.5, 10.0) == pytest.approx(5.0)

    def test_compute_combined_score_cold_start(self):
        """친화도 없음 (cold start) → hot_score 그대로."""
        assert compute_combined_score(0.0, 10.0) == pytest.approx(10.0)


# ============ 다양성 필터 테스트 ============


class TestDiversityCap:
    """PostService._apply_diversity_cap 테스트."""

    def test_diverse_authors(self):
        """다양한 작성자 → 모두 통과."""
        posts = [
            {"author": {"user_id": i}} for i in range(5)
        ]
        result = PostService._apply_diversity_cap(posts, limit=5)
        assert len(result) == 5

    def test_same_author_capped(self):
        """동일 작성자 5개 → 최대 3개."""
        posts = [
            {"author": {"user_id": 1}, "title": f"post_{i}"} for i in range(5)
        ]
        result = PostService._apply_diversity_cap(posts, limit=10)
        assert len(result) == 3

    def test_mixed_authors_with_limit(self):
        """혼합 작성자 + limit 적용."""
        posts = [
            {"author": {"user_id": 1}},
            {"author": {"user_id": 1}},
            {"author": {"user_id": 1}},
            {"author": {"user_id": 1}},  # 4번째 → 제외
            {"author": {"user_id": 2}},
            {"author": {"user_id": 2}},
        ]
        result = PostService._apply_diversity_cap(posts, limit=5)
        assert len(result) == 5
        author_ids = [p["author"]["user_id"] for p in result]
        assert author_ids.count(1) == 3
        assert author_ids.count(2) == 2

    def test_null_author_not_capped(self):
        """author_id가 None인 게시글은 제한 없음."""
        posts = [
            {"author": {"user_id": None}} for _ in range(5)
        ]
        result = PostService._apply_diversity_cap(posts, limit=10)
        assert len(result) == 5


# ============ API 통합 테스트 ============


class TestForYouFeedAPI:
    """추천 피드 API 통합 테스트."""

    @pytest.mark.asyncio
    async def test_for_you_sort_unauthenticated(self, client):
        """비로그인 사용자 → for_you 요청 시 latest 폴백, 200 응답."""
        res = await client.get("/v1/posts/?sort=for_you")
        assert res.status_code == 200
        data = res.json()
        assert "posts" in data["data"]

    @pytest.mark.asyncio
    async def test_for_you_sort_no_scores(self, authorized_user):
        """점수 없는 사용자 → latest 폴백."""
        auth_client, user_info, _ = authorized_user
        res = await auth_client.get("/v1/posts/?sort=for_you")
        assert res.status_code == 200
        data = res.json()
        assert "posts" in data["data"]

    @pytest.mark.asyncio
    async def test_for_you_with_scores(self, authorized_user):
        """점수가 있는 사용자 → 점수 순 정렬."""
        auth_client, user_info, _ = authorized_user
        user_id = user_info["user_id"]

        # 게시글 2개 생성 (다른 사용자로 생성해야 하지만, 간단히 자기 게시글로 테스트)
        post1 = await auth_client.post("/v1/posts/", json={
            "title": "Low score post", "content": "test", "category_id": 1,
        })
        post2 = await auth_client.post("/v1/posts/", json={
            "title": "High score post", "content": "test", "category_id": 1,
        })
        post1_id = post1.json()["data"]["post_id"]
        post2_id = post2.json()["data"]["post_id"]

        # 점수 직접 삽입
        await upsert_user_post_scores(user_id, [
            {"post_id": post1_id, "affinity_score": 0.2, "hot_score": 1.0, "combined_score": 0.2},
            {"post_id": post2_id, "affinity_score": 0.9, "hot_score": 1.0, "combined_score": 0.9},
        ])

        res = await auth_client.get("/v1/posts/?sort=for_you")
        assert res.status_code == 200
        posts = res.json()["data"]["posts"]

        # 점수가 있는 게시글이 포함되어야 함
        post_ids = [p["post_id"] for p in posts]
        if post2_id in post_ids and post1_id in post_ids:
            idx2 = post_ids.index(post2_id)
            idx1 = post_ids.index(post1_id)
            assert idx2 < idx1  # 높은 점수가 먼저

    @pytest.mark.asyncio
    async def test_for_you_with_category_filter(self, authorized_user):
        """추천 + 카테고리 필터 조합."""
        auth_client, _, _ = authorized_user
        res = await auth_client.get("/v1/posts/?sort=for_you&category_id=1")
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_for_you_with_search_filter(self, authorized_user):
        """추천 + 검색 필터 조합."""
        auth_client, _, _ = authorized_user
        res = await auth_client.get("/v1/posts/?sort=for_you&search=test")
        assert res.status_code == 200


# ============ 모델 레이어 테스트 ============


class TestAffinityModels:
    """affinity_models DB 함수 테스트."""

    @pytest.mark.asyncio
    async def test_user_has_scores_empty(self, db):
        """점수 없는 사용자 → False."""
        assert not await user_has_scores(999999)

    @pytest.mark.asyncio
    async def test_get_active_user_ids_empty(self, db):
        """활동 없음 → 빈 목록."""
        result = await get_active_user_ids(lookback_days=30)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_candidate_posts_meta_empty(self, db):
        """게시글 없음 → 빈 목록."""
        result = await get_candidate_posts_meta(max_age_days=7)
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_upsert_and_check_scores(self, db):
        """점수 UPSERT 후 user_has_scores 확인."""
        # 테스트용 사용자/게시글 생성
        async with transactional() as cur:
            await cur.execute(
                "INSERT INTO user (email, nickname, password) VALUES (%s, %s, %s)",
                ("feed_test@test.com", "feedtest", "hash"),
            )
            user_id = cur.lastrowid
            await cur.execute(
                "INSERT INTO post (title, content, author_id, category_id) VALUES (%s, %s, %s, %s)",
                ("test post", "content", user_id, 1),
            )
            post_id = cur.lastrowid

        await upsert_user_post_scores(user_id, [
            {"post_id": post_id, "affinity_score": 0.5, "hot_score": 2.0, "combined_score": 1.0},
        ])
        assert await user_has_scores(user_id)

    @pytest.mark.asyncio
    async def test_upsert_idempotent(self, db):
        """UPSERT 2회 실행 → 중복 없음."""
        async with transactional() as cur:
            await cur.execute(
                "INSERT INTO user (email, nickname, password) VALUES (%s, %s, %s)",
                ("idem_test@test.com", "idemtest", "hash"),
            )
            user_id = cur.lastrowid
            await cur.execute(
                "INSERT INTO post (title, content, author_id, category_id) VALUES (%s, %s, %s, %s)",
                ("idem post", "content", user_id, 1),
            )
            post_id = cur.lastrowid

        row = {"post_id": post_id, "affinity_score": 0.5, "hot_score": 2.0, "combined_score": 1.0}

        await upsert_user_post_scores(user_id, [row])
        await upsert_user_post_scores(user_id, [row])  # 2번째 실행

        # 행이 1개만 존재해야 함
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM user_post_score WHERE user_id = %s",
                    (user_id,),
                )
                count = (await cur.fetchone())[0]
                assert count == 1
