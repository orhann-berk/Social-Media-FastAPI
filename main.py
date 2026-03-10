import uvicorn
from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schemas import *
import crud
from db.database import get_db, engine, Base
from oauth2 import get_current_user, create_access_token
from db import models

app = FastAPI()
Base.metadata.create_all(bind=engine)


@app.get("/users/all", response_model=List[UserBaseModel], tags=["user"])
def get_users(
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user)
):
    result = crud.read_users(db)
    return result


@app.get("/user/{user_id}", tags=["user"])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user)
):
    return crud.get_user(db, user_id=user_id)


@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["user"])
def add_user(user: UserAuthModel, db: Session = Depends(get_db)):
    return crud.add_user(
        db,
        name=user.username,
        email=user.email,
        password=user.password,
    )


@app.post("/login", status_code=status.HTTP_200_OK, tags=["user"])
def login_user(form_data: OAuth2PasswordRequestForm = Depends(),
               db: Session = Depends(get_db)):

    user = crud.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(
        data={"sub": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/logout", tags=["user"], status_code=status.HTTP_200_OK)
def logout_user(
    _current_user: models.User = Depends(get_current_user)
):
    return {"message": "Logged out successfully"}


@app.delete("/user/{user_id}/delete", status_code=status.HTTP_202_ACCEPTED, tags=["user"])
def delete_user(user_id: int, db: Session = Depends(get_db), _current_user: models.User = Depends(get_current_user)):
    return crud.delete_user(db, user_id=user_id)


@app.put("/users/{user_id}/update", status_code=status.HTTP_202_ACCEPTED, tags=["user"])
def update_user(
    user: UserUpdateModel,
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    return crud.update_user(
        db,
        user_id=user_id,
        name=user.username,
        email=user.email,
        password=user.password
    )


@app.post("/friends/request/{receiver_id}", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED, tags=["friend-request"])
def send_friend_request(receiver_id: int, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)
                        ):
    return crud.create_friend_request(db=db, sender_id = current_user.id,
                                      receiver_id = receiver_id)


@app.get("/friend/requests/pending", response_model=List[FriendRequestResponse], tags=["friend-request"])
def get_pending_requests(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    User may see friend requests.
    """
    return crud.get_pending_requests(db=db, user_id = current_user.id)


@app.put("/friends/request/{request_id}/accept", response_model=FriendRequestResponse, tags=["friend-request"])
def accept_friend_request(request_id: int, db: Session = Depends(get_db)):
    return crud.accept_friend_request(db=db, request_id = request_id)


@app.put("/friends/request/{request_id}/reject", response_model=FriendRequestResponse, tags=["friend-request"])
def reject_friend_request(request_id: int, db=Depends(get_db)):
    return crud.reject_friend_request(db=db, request_id = request_id)


@app.get("/friends/{user_id}", response_model=List[UserBaseModel], tags=["friend-request"])
def get_friends(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id = user_id)
    if db_user == "User not found":
        raise HTTPException(status_code=404, detail="User not found!")

    return crud.list_friends(db=db, user_id = user_id)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )