from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
router = APIRouter()

#fake database
users=[]

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
class LoginRequest(BaseModel):
    email:EmailStr
    password:str
class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    bio: str | None = None

#get current user
def get_current_user(authorization: str | None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token")
    token = parts[1]

    try:
        user_id = int(token.replace("token-", ""))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    for u in users:
        if u["id"] == user_id:
            return u
    raise HTTPException(status_code=401, detail="User not found")

#Register
@router.post("/auth/register")
def register(data: RegisterRequest):
#To check if email already exist
    for u in users:
        if u["email"] == data.email:
            raise HTTPException(status_code=409, detail="Email already registered")
    new_user = {
        "id": len(users) + 1,
        "email": data.email,
        "password": data.password,
        "name": "",
        "bio":""
    }
    users.append(new_user)
    return{"id": new_user["id"], "email": new_user["email"]}

#login
@router.post("/auth/login")
def login(data: LoginRequest):
    for u in users:
        if u in users:
            if u["email"] == data.email:
                if u["password"] != data.password:
                    raise HTTPException(status_code=401, detail="Wrong email or password")

                token = f"token-{u['id']}"
                return {"access_token": token, "token_type": "bearer"}

        raise HTTPException(status_code=401, detail="Wrong email or password")

#ViewProfile
@router.get("/users/me")
def read_my_profile(authorization: str | None = Header(default=None)):
    u = get_current_user(authorization)
    return {"id": u["id"], "email": u["email"], "name": u["name"], "bio": u["bio"]}

#UpdateProfile
@router.put("/users/me")
def update_my_profile(
    data: ProfileUpdateRequest,
    authorization: str | None = Header(default=None),
):
    u = get_current-user(authorization)
    if data.name is not None:
        u["name"] = data.name
    if data.bio is not None:
        u["bio"] = data.bio
    return {
        "message": "Profile updated",
        "user": {
            "id": u["id"],
            "email": u["email"],
            "name": u["name"],
            "bio": u["bio"],
        },
    }
