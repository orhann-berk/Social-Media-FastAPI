from fastapi import FastAPI, HTTPException
from db.models import UserAuthModel
from fastapi.encoders import jsonable_encoder

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
    UserAuthModel.user_id = len(users)
    users.append(new_user)
    return {"user_id": user_id, "user": user}

@app.get("/login")
async def login_user(username: UserAuthModel.username, password: UserAuthModel.password):
    for user in users:
        if user["username"] == username and user["password"] == password:
            UserAuthModel.is_logged_in = True
            return {"message": "Login successful"}
        else:
            raise HTTPException(status_code=404, detail="Incorrect username or password")
    return None

@app.put("/update/{user_id}")
async def update_user(user_id: UserAuthModel.user_id, user: UserAuthModel):
    update_user_encoded = jsonable_encoder(user)
    users[user_id] = update_user_encoded
    return update_user_encoded