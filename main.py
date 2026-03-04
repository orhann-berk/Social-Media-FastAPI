import uvicorn
from typing import List
from fastapi import HTTPException, FastAPI, Depends, status
from sqlalchemy.orm import Session
from schemas import UserAuthModel, PostModel, UserBaseModel, PostCreate, PostOut, CommentCreate, CommentOut
import crud
from db.database import get_db, engine, Base
from db import models
Base.metadata.create_all(bind=engine)
from auth_utils import get_current_user


app = FastAPI()


@app.get("/users/all", response_model = List[UserBaseModel], tags=["users"]) #
def get_users(db: Session = Depends(get_db)):
    result = crud.read_users(db)
    return result


@app.get("/user/{user_id}", tags=["users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user(db, user_id = user_id)


@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["register"])
def add_user(user: UserAuthModel, db: Session = Depends(get_db)):
    return crud.add_user(db, name=user.name, email=user.email, password = user.password, is_logged_in = user.is_logged_in)


@app.post("/login", tags=["login/logout"])
def login_user(name: str, password: str, db: Session = Depends(get_db)):
    return crud.login_user(db, name = name, password = password)


@app.get("/logout", tags=["login/logout"])
def logout_user(name: str, password: str, db: Session = Depends(get_db)):
    return crud.logout_user(db, name = name, password = password)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["user/delete"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return crud.delete_user(db, user_id = user_id)


@app.put("/users/{user_id}", status_code=status.HTTP_202_ACCEPTED, tags=["user/update"])
def update_user(user: UserAuthModel, user_id:int, db: Session = Depends(get_db)):
    return crud.update_user(db, user_id= user_id, name = user.name, email = user.email, password=user.password)

@app.post("/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Post an activity to the authenticated user's personal wall."""
    post = models.Post(
        content=post_data.content,
        image_url=post_data.image_url,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post
@app.get("/wall/me", response_model=List[PostOut])
def get_my_wall(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get the authenticated user's own wall (all their posts)."""
    return (
        db.query(models.Post)
        .filter(models.Post.author_id == current_user.id)
        .order_by(models.Post.created_at.desc())
        .all()
    )



@app.get("/wall/{user_id}", response_model=List[PostOut])
def get_user_wall(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user's public wall."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return (
        db.query(models.Post)
        .filter(models.Post.author_id == user_id)
        .order_by(models.Post.created_at.desc())
        .all()
    )
@app.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(post)
    db.commit()
@app.post("/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = models.Comment(
        content=comment_data.content,
        post_id=post_id,
        author_id=current_user.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


if __name__ == "__main__":
    # Important: disable reload while debugging
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )

