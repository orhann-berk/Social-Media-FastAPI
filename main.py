from fastapi import FastAPI, HTTPException
from db.models import UserAuthModel, LoginUser

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
        if user["email"] == user.email:
            raise HTTPException(status_code=409, detail="Email already registered")
    # store the user
    new_user = {"user_id": len(users), "username": user.username, "email": user.email, "password": user.password}
    users.append(new_user)
    return {"user_id": user_id, "user": user}

@app.get("/login")
async def login(username: str, password: str):
    for user in users:
        if user["username"] == username and user["password"] == password:
            return {"message": "congratulations you successfully logged in"}
        else:
            raise HTTPException(status_code=404, detail="Incorrect username or password")
    return None