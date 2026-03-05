"""test_mention: 멘션 파싱 유틸리티 테스트."""

from utils.mention import extract_mentions


class TestExtractMentions:
    """extract_mentions() 함수 테스트."""

    def test_single_mention(self):
        assert extract_mentions("안녕 @홍길동 반가워") == ["홍길동"]

    def test_multiple_mentions(self):
        result = extract_mentions("@유저A 그리고 @유저B 안녕")
        assert result == ["유저A", "유저B"]

    def test_duplicate_mentions_deduplicated(self):
        result = extract_mentions("@홍길동 님 @홍길동 님")
        assert result == ["홍길동"]

    def test_no_mentions(self):
        assert extract_mentions("멘션 없는 텍스트") == []

    def test_empty_string(self):
        assert extract_mentions("") == []

    def test_mention_at_start(self):
        assert extract_mentions("@유저 안녕하세요") == ["유저"]

    def test_mention_at_end(self):
        assert extract_mentions("안녕하세요 @유저") == ["유저"]
