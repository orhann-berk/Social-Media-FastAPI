from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import current_user
from db.hash import Hash
from db.models import User
from fastapi import APIRouter, HTTPException, status
from oauth2 import create_access_token
from db import models

router = APIRouter(prefix="/posts", tags=["Posts"])

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not Hash.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    return user

def read_users(db: Session):
    retval = db.query(User).all()
    return retval


def get_user(db: Session, user_id: int):
    retval = db.query(User).filter(User.id == user_id).first()
    return retval


def add_user(db: Session, name:str, email:str, password:str):
    user = User(username = name, email = email, hashed_password = Hash.hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if current_user.is_logged_in:
        db.delete(user)
        db.commit()
        return HTTPException(status_code=status.HTTP_200_OK)
    else:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def update_user(db: Session, user_id: int, name: str, email: str, password: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user.is_logged_in:
        db_user.name = name
        db_user.email = email
        db_user.password = password
        db.commit()
        return HTTPException(status_code=status.HTTP_200_OK)
    else:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def login_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not Hash.verify(password, user.hashed_password):
     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}

# ─── Posts ───────────────────────────────────────────────────────────────────

def create_post(db: Session, content: str, image_url: str | None, author_id:int):
    post = models.Post(content=content, image_url=image_url, author_id=author_id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_post(db: Session, post_id: int):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


def get_posts_by_user(db: Session, user_id: int):
    return (
        db.query(models.Post)
        .filter(models.Post.author_id == user_id)
        .order_by(models.Post.created_at.desc())
        .all()
    )


def get_friends_feed(db: Session, friend_ids: list[int]):
    if not friend_ids:
        return []
    return (
        db.query(models.Post)
        .filter(models.Post.author_id.in_(friend_ids))
        .order_by(models.Post.created_at.desc())
        .all()
    )


def delete_post(db: Session, post: models.Post, current_user: models.User):
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(post)
    db.commit()


# ─── Comments ────────────────────────────────────────────────────────────────

def create_comment(db: Session, content: str, post_id: int, author_id: int):
    comment = models.Comment(content=content, post_id=post_id, author_id=author_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

