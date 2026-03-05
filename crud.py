from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from db.models import User, Post, Comment
from db.database import get_db
from db import models
from schemas import PostCreate, PostOut, CommentCreate, CommentOut
from auth_utils import get_current_user, verify_password

router = APIRouter(prefix="/posts", tags=["Posts"])

def read_users(db: Session):
    retval = db.query(User).all()
    return retval


def get_user(db: Session, user_id: int):
    retval = db.query(User).filter(User.id == user_id).first()
    return retval


def add_user(db: Session, name:str, email:str, password:str, is_logged_in: bool):
    user = User(username = name, email = email, hashed_password = password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user.is_logged_in:
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
    matching_user = db.query(User).filter(User.username == username).first()
    if matching_user:
        matching_user.is_logged_in = True
        db.commit()
        return HTTPException(status_code=status.HTTP_200_OK, detail="Login successful")
    else:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login unsuccessful")


def add_post(db: Session, title: str, body: str, image_url: str):
    post = Post(title = title, body = body, image_url = image_url)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def read_posts(db:Session, ):
    retval = db.query(Post).all()
    return retval


def logout_user(db: Session, name: str, password: str):
    user_out = db.query(User).filter(User.name == name and User.hashed_password == password and User.is_logged_in == bool[True]).first()
    if user_out:
        user_out.is_logged_in= False
        db.commit()
        return HTTPException(status_code=status.HTTP_200_OK)
    else:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

# ─── Create Post ────────────────────────────────────────────────────────────
@router.post("/posts", response_model=PostOut)
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


# ─── Get My Wall ───────────────────────────────────────────────────────────────
@router.get("/me", response_model=List[PostOut])
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

# ─── Get User Wall ────────────────────────────────────────
@router.get("/user/{user_id}", response_model=List[PostOut])
def get_user_wall(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return (
        db.query(models.Post)
        .filter(models.Post.author_id == user_id)
        .order_by(models.Post.created_at.desc())
        .all()
    )
# ─── Delete Post ─────────────────────────────────────────────────────────────
@router.delete("/{post_id}")
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
    return {"message": "Post deleted"}

# ─── Add Comments ─────────────────────────────────────────────────────────────────
@router.post("/{post_id}/comments", response_model=CommentOut)
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
