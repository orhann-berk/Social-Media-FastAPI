from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()

#this is a fake database just for now
users=[]

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/auth/register")
def register(data: RegisterRequest):
#To check if email already exist
    for u in users:
        if u["email"] == data.email:
            raise HTTPException(status_code=409, detail="Email already registered")
#store the user
    new_user = {"id": len(users) + 1, "email": data.email, "password": data.password}
    users.append(new_user)

    return{"id": new_user["id"], "email": new_user["email"]}

