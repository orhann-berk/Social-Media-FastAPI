from fastapi import FastAPI
app = FastAPI()
@app.get("/")
async def root():
    return {"message": "we can start now"}

@app.get("/register")
async def register(username: str, email:str, password: str):
    return {"username": username, "email": email, "password": password}