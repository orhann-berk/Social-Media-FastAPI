import uvicorn
from typing import List
from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session
from schemas import *
import crud
from db.database import get_db

app = FastAPI()


@app.get("/user/all", status_code=status.HTTP_200_OK, response_model = List[UserBaseModel], tags=["user"]) #
def get_users(db: Session = Depends(get_db)):
    result = crud.read_users(db)
    return result


@app.get("/user/{user_id}", status_code=status.HTTP_200_OK, tags=["user"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user(db, user_id = user_id)


@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["user"])
def add_user(user: UserAuthModel, db: Session = Depends(get_db)):
    return crud.add_user(db, name=user.name, email=user.email, password = user.password)


@app.get("/login", status_code=status.HTTP_200_OK, tags=["user"])
def login_user(name: str, password: str, db: Session = Depends(get_db)):
    return crud.login_user(db, name = name, password = password)


@app.get("/logout", tags=["user"], status_code=status.HTTP_200_OK)
def logout_user(name: str, password: str, db: Session = Depends(get_db)):
    return crud.logout_user(db, name = name, password = password)


@app.delete("/user/{user_id}/delete", status_code=status.HTTP_202_ACCEPTED, tags=["user"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return crud.delete_user(db, user_id = user_id)


@app.put("/users/{user_id}/update", status_code=status.HTTP_202_ACCEPTED, tags=["user"])
def update_user(user: UserUpdateModel, user_id:int, db: Session = Depends(get_db)):
    return crud.update_user(db, user_id= user_id, name = user.name, email = user.email, password=user.password)


@app.post("/add/post", status_code=status.HTTP_202_ACCEPTED, tags=["posts"])
def add_post(post: PostModel, db: Session = Depends(get_db)):
    return crud.add_post(db, title = post.title, body = post.body, image_url= post.image_url)


@app.get("/posts", status_code=status.HTTP_200_OK, tags=["posts"])
def get_posts(db: Session = Depends(get_db)):
    result = crud.read_posts(db)
    return result

@app.post("/friends/request", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED, tags=["friend-request"])
def send_friend_request(request: FriendRequestCreate, db: Session = Depends(get_db)):
    return crud.create_friend_request(
        db=db, sender_id=request.sender_id, receiver_id=request.receiver_id)

@app.get("/friend/requests/pending/{user_id}", response_model=List[FriendRequestResponse], tags=["friend-request"])
def get_pending_requests(user_id: int, db: Session = Depends(get_db)):
    """
    User may see friend requests.
    """
    return crud.get_pending_requests(db=db, user_id = user_id)


if __name__ == "__main__":
    # Important: disable reload while debugging
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )

