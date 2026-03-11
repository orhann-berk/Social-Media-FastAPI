import uvicorn
from typing import List
from fastapi import HTTPException, FastAPI, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schemas import UserAuthModel, UserBaseModel, TopicModel, DiscussionModel, AddTopicModel, AddMemberModel, \
    AddAdminModel
import crud
from db.database import get_db, engine, Base
from Posts import router as posts_router
from db.hash import Hash
from oauth2 import get_current_user, create_access_token
from db import models

app = FastAPI()
app.include_router(posts_router)

Base.metadata.create_all(bind=engine)


@app.get("/users/all", response_model=List[UserBaseModel], tags=["user"])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = crud.read_users(db)
    return result


@app.get("/user/{user_id}", tags=["user"])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {"message": "Logged out successfully"}


@app.delete("/user/{user_id}/delete", status_code=status.HTTP_202_ACCEPTED, tags=["user"])
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.delete_user(db, user_id=user_id)


@app.put("/users/{user_id}/update", status_code=status.HTTP_202_ACCEPTED, tags=["user"])
def update_user(
    user: UserAuthModel,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.update_user(
        db,
        user_id=user_id,
        name=user.username,
        email=user.email,
        password=user.password
    )


@app.post("/topic/add", status_code=status.HTTP_201_CREATED, tags=["topics"])
def add_topic(topic: AddTopicModel,
              db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    return crud.add_topic(db, topic.title, current_user.id)


@app.get("/topic/all", status_code = status.HTTP_200_OK,response_model=List[TopicModel], tags=["topics"])
def get_topics(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    result = crud.read_topics(db)
    return result


@app.post("/topics/{topic_id}/discussion", status_code=status.HTTP_201_CREATED, tags=["topics"])
def add_disc(
        topic_id: int,
        disc: DiscussionModel,
        db:Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    return crud.add_disc(db, name= disc.name, topic_id = topic_id, current_user_id = current_user.id)


@app.get("/topics/{topic_id}/discussion/all", status_code = status.HTTP_200_OK, tags=["topics"])
def get_disc(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    result = crud.read_disc(db)
    return result


@app.post("/topics/{topic_id}/add-admin", status_code=status.HTTP_201_CREATED, tags=["topics"])
def add_admin_to_topic(
        topic_id:int,
        admin_data: AddAdminModel,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    return crud.add_admin_to_topic(db, topic_id, admin_data.user_id, current_user.id)


@app.post("/topics/{topic_id}/add-member", status_code=status.HTTP_201_CREATED, tags=["topics"])
def add_member_to_topic(
        topic_id: int,
        member: AddMemberModel,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user),
):
    return crud.add_member_to_topic(db, topic_id, member.user_id, current_user.id)





if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )
