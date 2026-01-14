from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    email: str
    password: str
    nickname: str
    profileImageUrl: str = "/assets/default_profile.png"


_users = [
    User(
        id=1,
        name="Alice",
        email="alice@test.com",
        password="password",
        nickname="pietro",
    ),
    User(
        id=2,
        name="Bob",
        email="bob@test.com",
        password="password",
        nickname="bob",
    ),
    User(
        id=3,
        name="Chris",
        email="chris@test.com",
        password="password",
        nickname="chris",
    ),
]


# 모든 유저의 목록
def get_users():
    return _users.copy()


# ID로 유저 조회
def get_user_by_id(user_id: int):
    return next((u for u in _users if u.id == user_id), None)


# 이메일로 유저 조회
def get_user_by_email(email: str):
    return next((u for u in _users if u.email == email), None)


# 닉네임으로 유저 조회
def get_user_by_nickname(nickname: str):
    return next((u for u in _users if u.nickname == nickname), None)


def add_user(user: User):
    _users.append(user)
    return user
