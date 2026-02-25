import uvicorn
from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session
from schemas import UserAuthModel, UserBaseModel, PostModel
import crud
from typing import List
from database import get_db

app = FastAPI()

# USER ADD, UPDATE, DELETE AND GET OPERATIONS.
@app.get("/users") # , response_model = List[UserBaseModel]
def get_users(db: Session = Depends(get_db)):
    result = crud.read_users(db)
    return result

@app.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user(db, user_id = user_id)


@app.post("/register", status_code=status.HTTP_201_CREATED)
def post_user(user: UserAuthModel, db: Session = Depends(get_db)):
    return crud.post_user(db, name=user.name, email=user.email, password = user.password)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return crud.delete_user(db, user_id = user_id)


@app.put("/users/{user_id}", status_code=status.HTTP_202_ACCEPTED)
def update_user(user: UserAuthModel, user_id:int, db: Session = Depends(get_db)):
    return crud.update_user(db, user_id= user_id, name = user.name, email = user.email, password=user.password)


# @app.post("/users/{user_id}", status_code=status.HTTP_202_ACCEPTED)
# def add_post(post: PostModel, db: Session = Depends(get_db)):
#     return crud.add_post(db, post =)


if __name__ == "__main__":
    # Important: disable reload while debugging
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )