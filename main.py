from fastapi import FastAPI, HTTPException
from db.models import UserAuthModel

app = FastAPI()

# python list for use of db
users = []

@app.get("/")
async def root():
    return {"message": "we can start now"}

@app.post("/register")
async def register(user_id: int, user: UserAuthModel):
    # check if email already exist
    for user in users:
        if user["email"] == UserAuthModel.email:
            raise HTTPException(status_code=409, detail="Email already registered")
    # store the user
    new_user = {"user_id": len(users), "username": UserAuthModel.username, "email": UserAuthModel.email, "password": UserAuthModel.password}
    users.append(new_user)
    return {"user_id": user_id, "user": user}