# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

커뮤니티 백엔드 API 서버 (AWS AI School 2기 3주차 과제). FastAPI 기반의 비동기 Python 백엔드로, MySQL 데이터베이스와 세션 기반 인증을 사용합니다.

## Commands

```bash
# 서버 실행
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 8000

# 테스트 실행
pytest                    # 전체 테스트
pytest tests/test_qa_full.py::test_name  # 단일 테스트

# 린팅 & 타입 체크
ruff check .
mypy .

# 개발 의존성 설치
pip install -e ".[dev]"
```

## Architecture

**Router → Controller → Model 계층 구조**

```text
main.py                    # 앱 진입점, 미들웨어/라우터 등록
├── routers/               # API 엔드포인트 정의 (/v1/auth, /v1/users, /v1/posts, /v1/terms)
├── controllers/           # 비즈니스 로직
├── services/              # 컨트롤러-모델 간 조율 (user_service, post_service)
├── models/                # 데이터베이스 쿼리 (aiomysql 직접 사용)
├── schemas/               # Pydantic 요청/응답 모델
├── dependencies/          # FastAPI 의존성 주입 (인증, 컨텍스트)
├── middleware/            # 로깅, 타이밍, Rate Limiting, 예외 처리
├── utils/                 # 비밀번호(bcrypt), 파일 업로드, HTTP 에러 헬퍼, 포매터
├── core/config.py         # pydantic-settings 기반 설정 (.env 로드)
├── database/              # 커넥션 풀(connection.py), 스키마(schema.sql), 마이그레이션
└── tests/                 # pytest 테스트 (conftest, test_qa_full, test_auth, test_rate_limiter)
```

**주요 특징:**
- 세션 기반 인증 (JWT 미사용), 24시간 만료
- bcrypt 비밀번호 해싱
- 트랜잭션 데코레이터 (`@transactional()`)
- Soft delete 패턴 (user 탈퇴 시 `deleted_at` 사용)
- 정적 파일: `/assets` (posts/, profiles/)

## Database

MySQL 비동기 연결 (aiomysql). 스키마는 `database/schema.sql` 참조.

주요 테이블: `user`, `user_session`, `post`, `comment`, `post_like`, `image`, `post_view_log`

마이그레이션 파일: `database/migration_001~999_*.sql` — 인덱스 추가 및 성능 최적화

## Environment Variables

`.env` 파일 필수 (`.env.example` 참조):
- `SECRET_KEY`: 세션 암호화 키
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: MySQL 연결 정보

## API Endpoints

모든 API는 `/v1/` 프리픽스 사용:

- `/v1/auth` - 로그인, 로그아웃, 인증 상태
- `/v1/users` - 프로필, 비밀번호 변경, 회원 탈퇴
- `/v1/posts` - CRUD, 좋아요, 댓글
- `/v1/terms` - 이용약관
- `/health` - 헬스체크

## Gotchas

- **Rate Limiting**: IP당 30회/분 제한 (`middleware/rate_limiter.py`). 테스트 시 `TESTING=true` 환경변수로 비활성화
- **Soft Delete 쿼리**: `user`, `post`, `comment` 조회 시 반드시 `WHERE deleted_at IS NULL` 조건 필요. 누락하면 삭제된 데이터 노출
- **트랜잭션 패턴**: 다중 테이블 변경 시 `async with transactional() as cur:` 또는 `@transactional()` 데코레이터 사용. `database/connection.py` 참조
- **미들웨어 파일명**: 로깅 미들웨어 파일은 `middleware/logging.py` (Python 표준 `logging` 모듈과 이름 충돌 가능 — 임포트 시 주의)
- **타이밍 공격 방지**: `auth_controller.py`에서 존재하지 않는 유저에도 bcrypt 검증을 수행. 이 패턴을 제거하면 안 됨
- **이미지 업로드 검증**: `utils/file_utils.py`에서 확장자 + 매직넘버(파일 시그니처) 이중 검증. 확장자만 체크하면 안전하지 않음
