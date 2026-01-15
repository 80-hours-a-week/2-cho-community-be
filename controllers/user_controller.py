from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
from models import user_models
import re
import uuid


# 유저 조회하기 (/v1/users/{nickname})
async def get_user(request: Request):
    try:
        nickname = request.path_params.get("nickname")
        if not nickname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_nickname",
            )
        user = user_models.get_user_by_nickname(nickname)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user_not_found",
            )

        content = {
            "code": "AUTH_SUCCESS",
            "message": "사용자 조회에 성공했습니다.",
            "data": {
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "nickname": user.nickname,
                    "profileImageUrl": user.profileImageUrl,
                }
            },
            "errors": [],
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        return JSONResponse(
            content=content,
            status_code=status.HTTP_200_OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trackingID": str(uuid.uuid4()),
                "error": str(e),
            },
        )


# 유저 생성하기 (/v1/users)
async def create_user(request: Request):
    try:
        body = await request.json()
        name = body.get("name")
        email = body.get("email")
        password = body.get("password")
        nickname = body.get("nickname")
        profileImageUrl = body.get("profileImageUrl")
        if not profileImageUrl:
            profileImageUrl = "/assets/default_profile.png"

        # 데이터 누락
        if not name or not email or not password or not nickname or not profileImageUrl:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="missing_required_fields",
            )

        if (
            not isinstance(name, str)
            or not isinstance(email, str)
            or not isinstance(password, str)
            or not isinstance(nickname, str)
            or not isinstance(profileImageUrl, str)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_field_types",
            )

        # 이미지 파일 검사 - 1. 확장자 검사 (단순 문자열 형식 검증)
        allowed_extensions: set[str] = {".jpg", ".jpeg", ".png"}
        if not any(profileImageUrl.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_image_format",
            )

        # 요청 메소드는 반드시 POST여야 함.
        if request.method != "POST":
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="method_not_allowed",
            )

        if user_models.get_user_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email_already_exists",
            )
        if user_models.get_user_by_nickname(nickname):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="nickname_already_exists",
            )

        # 이미지 파일 검사 - 2. MIME 타입 검증: (보류 - URL/스트링 기반으로는 서버측 검증이 복잡함)
        # 현재는 단순 확장자 검사만 수행합니다.

        # 이메일 형식 검사 (정규표현식)
        if not re.match(r"^[^@]+@[^@]+\.[^@]+", email):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="invalid_email_format",
            )

        # 비밀번호 형식 검사 (정규표현식)
        if not re.match(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$",
            password,
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="invalid_password_format",
            )

        # 닉네임 형식 검사 (정규표현식)
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", nickname):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="invalid_nickname_format",
            )

        content = {
            "code": "SIGNUP_SUCCESS",
            "message": "사용자 생성에 성공했습니다.",
            "data": {},
            "errors": [],
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        new_user = user_models.User(
            id=len(user_models.get_users()) + 1,
            name=name,
            email=email,
            password=password,
            nickname=nickname,
            profileImageUrl=profileImageUrl,
        )
        user_models.add_user(new_user)

        return JSONResponse(
            content=content,
            status_code=status.HTTP_201_CREATED,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trackingID": str(uuid.uuid4()),
                "error": str(e),
            },
        )


# 내 정보 조회하기 (/v1/users/me)
async def get_my_info(request: Request):
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized",
            )

        email = request.session.get("email")
        user = user_models.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied",
            )

        if request.method != "GET":
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Method Not Allowed",
            )

        content = {
            "code": "AUTH_SUCCESS",
            "message": "현재 로그인 중인 상태입니다.",
            "data": {
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "profileImageUrl": user.profileImageUrl,
                },
            },
            "errors": [],
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return JSONResponse(
            content=content,
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trackingID": str(uuid.uuid4()),
                "error": str(e),
            },
        )


# 유저 정보 조회하기 (/v1/users/{nickname})
async def get_user_info(request: Request):
    try:
        # 로그인한 상태인지 확인
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized",
            )

        email = request.session.get("email")
        user = user_models.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied",
            )

        nickname = request.path_params.get("nickname")
        user = user_models.get_user_by_nickname(nickname)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        content = {
            "code": "QUERY_SUCCESS",
            "message": "유저 조회에 성공했습니다.",
            "data": {
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "profileImageUrl": user.profileImageUrl,
                },
            },
            "errors": [],
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return JSONResponse(
            content=content,
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trackingID": str(uuid.uuid4()),
                "error": str(e),
            },
        )


# 내 정보 수정하기 (/v1/users/me)
async def update_user(request: Request):
    try:
        body = await request.json()
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized",
            )

        # 세션에서 현재 로그인한 사용자 정보 가져오기
        current_email = request.session.get("email")
        current_user = user_models.get_user_by_email(current_email)

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user_not_found",
            )

        if request.method != "PATCH":
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="method_not_allowed",
            )

        # 변경할 데이터 확인
        nickname = body.get("nickname")

        # 변경사항이 없는 경우
        if not nickname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="no_changes_provided",
            )

        # 1. 닉네임 형식 검사 (정규표현식)
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", nickname):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="invalid_nickname_format",
            )

        # 2. 닉네임 중복 검사 (본인 닉네임인 경우 제외)
        existing_user = user_models.get_user_by_nickname(nickname)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="nickname_already_exists",
            )

        # 모델 업데이트 호출
        updated_user = user_models.update_user(current_user.id, nickname=nickname)

        # 세션 정보도 업데이트 (필요한 경우)
        request.session["nickname"] = updated_user.nickname

        content = {
            "code": "UPDATE_SUCCESS",
            "message": "유저 정보 수정에 성공했습니다.",
            "data": {
                "user": {
                    "user_id": updated_user.id,
                    "email": updated_user.email,
                    "nickname": updated_user.nickname,
                    "profileImageUrl": updated_user.profileImageUrl,
                }
            },
            "errors": [],
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return JSONResponse(
            content=content,
            status_code=status.HTTP_200_OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trackingID": str(uuid.uuid4()),
                "error": str(e),
            },
        )
