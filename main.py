from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

users = [
    {"id": 1, "name": "Alice", "email": "alice@test.com"},
    {"id": 2, "name": "Bob", "email": "bob@test.com"},
]

origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="invalid_user_id")

    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"data": user}


@app.post("/users", status_code=201)
def create_user(data: dict):
    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        raise HTTPException(status_code=400, detail="missing_required_fields")
    if any(u["email"] == email for u in users):
        raise HTTPException(status_code=409, detail="email_already_exists")

    new_user = {"id": len(users) + 1, "name": name, "email": email}
    users.append(new_user)
    return {"data": new_user}


@app.post("/login")
def login(data: dict):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="missing_email")

    user = next((u for u in users if u["email"] == email), None)
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")

    return {"data": {"user_id": user["id"], "name": user["name"]}}
