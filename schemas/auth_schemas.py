"""auth_schemas: 인증 관련 Pydantic 모델 모듈.

로그인, 로그아웃 요청/응답 스키마를 정의합니다.
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """로그인 요청 모델.

    Attributes:
        email: 사용자 이메일 주소.
        password: 비밀번호.
    """

    email: EmailStr
    password: str


class LogoutResponse(BaseModel):
    """로그아웃 응답 모델.

    Attributes:
        code: 응답 코드.
        message: 응답 메시지.
    """

    code: str = "LOGOUT_SUCCESS"
    message: str = "로그아웃에 성공했습니다."
