from dataclasses import dataclass, replace


@dataclass(frozen=True)
class User:
    id: int
    name: str
    email: str
    password: str
    nickname: str
    profileImageUrl: str = "/assets/default_profile.png"
    is_active: bool = True


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


# 사용자 추가하기
def add_user(user: User):
    _users.append(user)
    return user


# 사용자 정보 업데이트 (기존 정보 삭제 후 새로운 사용자로 추가)
def update_user(user_id: int, **kwargs):
    for i, user in enumerate(_users):
        if user.id == user_id:
            # 기존 유저 정보를 바탕으로 새로운 유저 객체 생성 (불변성 유지)
            updated_user = replace(user, **kwargs)
            _users[i] = updated_user
            return updated_user
    return None
