from fastapi import FastAPI, HTTPException
from db.models import UserAuthModel
from fastapi.encoders import jsonable_encoder

app = FastAPI()

# python list for use of db
users = []

@app.get("/")
async def root():
    return {"message": "welcome"}

@app.post("/register")
async def register(user_id: int, user: UserAuthModel):
    # check if email already exist
    for u in users:
        if u["email"] == user.email:
            raise HTTPException(status_code=409, detail="Email already registered")
        elif u["username"] == user.username:
            raise HTTPException(status_code=409, detail="Username already registered")
    # store the user
    new_user = {"list_index": len(users), "username": user.username, "email": user.email, "password": user.password, "is_logged_in": user.is_logged_in}
    users.append(new_user)
    return {"user_id": user_id, "user": user}

@app.get("/login")
async def login_user(username: str, password: str):
    for u in users:
        if u["username"] == username and u["password"] == password:
            return {"message": "Login successful"}
        else:
            raise HTTPException(status_code=404, detail="Incorrect username or password")
    return None

@app.put("/update/{user_id}")
async def update_user(user_id: int, user: UserAuthModel):
    update_user_encoded = jsonable_encoder(user)
    users[user_id] = update_user_encoded
    return update_user_encoded