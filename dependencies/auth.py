"""auth: FastAPI 의존성 주입을 위한 인증 모듈.

세션 기반 사용자 인증 및 권한 확인 기능을 제공합니다.
"""

from datetime import datetime
from fastapi import HTTPException, Request, status
from models import user_models
from models.user_models import User


async def get_current_user(request: Request) -> User:
    """세션에서 현재 사용자를 추출하고 검증합니다.

    세션에 저장된 이메일로 사용자를 조회하여 반환합니다.

    Args:
        request: FastAPI Request 객체.

    Returns:
        인증된 사용자 객체.

    Raises:
        HTTPException: 세션이 없으면 401, 사용자가 없으면 403.
    """
    session_id = request.session.get("session_id")

    # 세션이 존재하지 않음
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )

    # DB에서 세션과 사용자 정보를 한 번에 조회 (JOIN 사용)
    result = await user_models.get_user_and_session(session_id)

    # 세션이나 사용자가 존재하지 않음 (Strict Validation)
    if not result:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )

    expires_at = result["expires_at"]
    user = result["user"]

    # 세션 만료 확인
    if expires_at < datetime.now():
        await user_models.delete_session(session_id)
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "session_expired",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )

    # 사용자 정보를 찾을 수 없음 (탈퇴했거나 DB에서 삭제됨) - JOIN으로 이미 체크되었지만 명시적 확인
    # get_user_and_session이 user 객체를 반환했으면 user는 존재함.
    # 하지만 withdraw 로직에서 soft delete된 경우 user는 존재하지만 deleted_at이 set 되어있을 수 있음.
    # 다만 기존 로직은 user를 가져와서 체크하지 않고 not user일때만 체크했음.
    # withdraw_user는 세션을 삭제하므로 여기 도달 안함.
    # 하지만 안전을 위해 check?
    # 기존 코드: user = get_user_by_email -> if not user: raise
    # get_user_by_email implementation: returns User even if deleted_at is set?
    # Let's check get_user_by_email in user_models.py (usually checks deleted_at IS NULL).
    # Assuming get_user_and_session also needs to filter deleted_at.
    # My SQL query selected everything.
    # Wait, the inner join relies on user existing.
    # If I want to exclude deleted users, I should add AND u.deleted_at IS NULL to the query or check here.
    # Let's check here for clarity, or update the query.
    # Updating the query is better for performance (don't return data if deleted).
    # But I already wrote the query without deleted_at check?
    # Actually the `get_user_and_session` query does NOT check `deleted_at IS NULL`.
    # So I should check it here.

    if user.deleted_at:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )

    return user


async def get_optional_user(request: Request) -> User | None:
    """선택적으로 현재 사용자를 추출합니다.

    인증되지 않은 요청에서도 에러를 발생시키지 않고 None을 반환합니다.

    Args:
        request: FastAPI Request 객체.

    Returns:
        인증된 사용자 객체, 인증되지 않은 경우 None.
    """
    session_id = request.session.get("session_id")

    # 세션이 존재하지 않으면 None 반환
    if not session_id:
        return None

    # DB 세션과 사용자 확인
    result = await user_models.get_user_and_session(session_id)
    if not result:
        return None

    expires_at = result["expires_at"]
    user = result["user"]

    # 만료 확인
    if expires_at < datetime.now():
        return None

    # 삭제된 사용자 확인
    if user.deleted_at:
        return None

    return user
