from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy.sql.functions import current_user
from db.hash import Hash
from db.models import User, DbFriendRequest, RequestStatus
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
    if retval:
        return retval
    return "No users found"

def get_user(db: Session, user_id: int):
    retval = db.query(User).filter(User.id == user_id).first()
    if retval:
        return retval
    return  "User not found"

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
        return "User deleted"
    else:
        return "User must login"

def update_user(db: Session, user_id: int, name: str, email: str, password: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return "User not found"
    elif db_user.is_logged_in:
        db_user.name = name
        db_user.email = email
        db_user.password = password
        db.commit()
        return "User updated successfully"
    else:
        return "User must login"

def login_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not Hash.verify(password, user.hashed_password):
     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}

def logout_user(db: Session, name: str, password: str):
    user_out = db.query(User).filter(User.username == name, User.hashed_password == Hash.hash_password(password)).first()
    if not user_out:
        return "User cannot found"
    elif user_out.is_logged_in:
        user_out.is_logged_in= False
        db.commit()
        return "Logout successful"
    elif not user_out.is_logged_in:
        return "User must login"
    else:
        return "Logout unsuccessful"

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

def create_comment(db: Session, content: str, post_id: int, author_id: int):
    comment = models.Comment(content=content, post_id=post_id, author_id=author_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def create_friend_request(db: Session, sender_id: int, receiver_id: int):
    if sender_id == receiver_id:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="You can not send a friend request to yourself.")

    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Receiver does not exist.")

    existing_request = db.query(DbFriendRequest).filter(
        or_(
            and_(DbFriendRequest.sender_id == sender_id, DbFriendRequest.receiver_id == receiver_id),
            and_(DbFriendRequest.receiver_id == sender_id, DbFriendRequest.sender_id == receiver_id)
        )
    ).first()

    if existing_request:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="You have already sent a friend request to this user.")

    new_request = DbFriendRequest(sender_id = sender_id, receiver_id = receiver_id,
                                  status=RequestStatus.pending)

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request

def get_pending_requests(db: Session, user_id: int):
    requests = db.query(DbFriendRequest).filter(DbFriendRequest.receiver_id == user_id,
                                                DbFriendRequest.status == RequestStatus.pending).all()

    return requests

def accept_friend_request(db: Session, request_id: int, user_id: int):
    friend_request = db.query(DbFriendRequest).filter(DbFriendRequest.id == request_id).first()
    if not friend_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="This request does not exist.")

    if friend_request.receiver_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can not answer this request!")


    if friend_request.status != RequestStatus.pending:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="This request has already accepted.")

    friend_request.status = RequestStatus.accepted
    db.commit()
    db.refresh(friend_request)
    return friend_request

def reject_friend_request(db: Session, request_id: int, user_id: int):
    friend_request = db.query(DbFriendRequest).filter(DbFriendRequest.id == request_id).first()

    if not friend_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="This request does not exist.")

    if friend_request.receiver_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can not answer this request!")

    if friend_request.status != RequestStatus.pending:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="You already replied to this request.")

    friend_request.status = RequestStatus.rejected
    db.commit()
    db.refresh(friend_request)
    return friend_request

def list_friends(db: Session, user_id: int):
    requests_as_sender = db.query(DbFriendRequest).filter(DbFriendRequest.status == RequestStatus.accepted,
                                                          DbFriendRequest.sender_id == user_id).all()

    requests_as_receiver = db.query(DbFriendRequest).filter(DbFriendRequest.status == RequestStatus.accepted,
                                                            DbFriendRequest.receiver_id == user_id).all()

    all_friends = requests_as_receiver + requests_as_sender

    friends_ids = []
    for request in all_friends:
        if request.sender_id == user_id:
            friends_ids.append(request.receiver_id)
        else:
            friends_ids.append(request.sender_id)

    if not friends_ids:
        return []

    friends = db.query(User).filter(User.id.in_(friends_ids)).all()
    return friends