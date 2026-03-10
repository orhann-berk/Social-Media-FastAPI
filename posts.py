from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from schemas import PostCreate, PostOut, CommentCreate, CommentOut
from oauth2 import get_current_user
from db import models
import crud

router = APIRouter(prefix="/posts", tags=["Posts"])


# ─── Create Post ─────────────────────────────────────────────────────────────

@router.post("/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
        post: PostCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    return crud.create_post(db, post.content, post.image_url, current_user.id)


# ─── Own Wall ────────────────────────────────────────────────────────────────

@router.get("/wall/me", response_model=List[PostOut])
def get_my_wall(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Post)
        .filter(models.Post.author_id == current_user.id)
        .order_by(models.Post.created_at.desc())
        .all()
    )


# ─── Any User's Wall ─────────────────────────────────────────────────────────

@router.get("/wall/{user_id}", response_model=List[PostOut])
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


# ─── Delete Post ─────────────────────────────────────────────────────────────

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    db.delete(post)
    db.commit()


# ─── Comments ────────────────────────────────────────────────────────────────

@router.post("/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
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
