import uuid
from fastapi import Request, Response, HTTPException, status
from datetime import datetime
from models import user_models


async def get_my_info(request: Request):
    print(f"auth_me: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    return None


async def login(request: Request):
    body = await request.json()
    email = body.get("email")
    password = body.get("password")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="missing_email"
        )
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="missing_password"
        )

    user = user_models.get_user_by_email(email)

    if not user or not user["password"] == password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )

    session_id = request.session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
        request.session["user_id"] = user["id"]

    print(f"login: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}")

    return {
        "data": {
            "session_id": session_id,
            "user_id": user["id"],
            "name": user["name"],
        },
    }


async def logout(request: Request):
    try:
        request.session.clear()
        print(f"logout: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    return None
