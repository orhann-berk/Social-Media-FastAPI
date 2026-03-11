from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from db.models import DbFriendRequest, RequestStatus
from db.hash import Hash
from db.models import User, Discussion, Topic, Admin
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
    if retval:
        return retval
    return "No users found"

def get_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def add_user(db: Session, name:str, email:str, password:str):
    user = User(username = name, email = email, hashed_password = Hash.hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



def delete_user(db: Session, user_id: int, current_user: User):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted."}


def update_user(db: Session, user_id: int, name: str, email: str, password: str, current_user: User):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own account")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.username = name
    db_user.email = email
    db_user.hashed_password = Hash.hash_password(password)

    db.commit()
    db.refresh(db_user)

    return {"message": "User updated. Please login again."}


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


def add_topic(db: Session, title:str, user_id:int):
    # create new topic
    new_topic = Topic(title= title)
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)

    # find admin record relation with user
    admin = db.query(Admin).filter(Admin.user_id == user_id).first()

    # if there is no admin record make a new one
    if not admin:
        user = db.query(User).filter(User.id == user_id).first()


        admin = Admin(
            user_id=user_id,
            name=user.username
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # do the relation from admin to topic
    new_topic.admins.append(admin)
    db.commit()
    db.refresh(new_topic)

    return new_topic


def add_member_to_topic(db:Session, topic_id: int, user_id: int, current_user_id: int):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # check if admin exists
    admin = db.query(Admin).filter(Admin.user_id == current_user_id).first()
    if not admin or admin not in topic.admins:
        raise HTTPException(status_code=403, detail="You are not admin of this topic")

    # check if added user exists
    user =db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user not in topic.members:
        topic.members.append(user)
        db.commit()
        db.refresh(topic)

    return topic


def add_admin_to_topic(db:Session, topic_id: int, user_id: int, current_user_id: int):
    # take the topic data and add admin to topic
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # fetch the current admin with auth
    current_admin = db.query(Admin).filter(Admin.user_id == current_user_id).first()
    if not current_admin or current_admin not in topic.admins:
        raise HTTPException(status_code=403, detail="You are not admin of this topic")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # take the user id and find user by it and add as an admin to the topic
    new_admin = db.query(Admin).filter(Admin.user_id == user_id).first()
    # if there is no record in admin table, add it based on user_id
    if not new_admin:
        new_admin = Admin(
            user_id = user.id,
            name = user.username
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

    if new_admin not in topic.admins:
        topic.admins.append(new_admin)
        db.commit()
        db.refresh(topic)

    return topic


def read_topics(db: Session):
    retval = db.query(Topic).all()
    if retval:
        return retval
    raise HTTPException(status_code=404, detail="No topics found")


def get_topic_by_id(db: Session, topic_id: int):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return topic


def add_disc(db: Session, name: str, topic_id: int, current_user_id: int):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    #  we fetch user, only members can add discussions
    user = db.query(User).filter(User.id == current_user_id).first()
    # check if the user on the members
    if user not in topic.members:
        raise HTTPException(status_code=403, detail="Only members can add discussion")

    new_disc = Discussion(name = name)
    topic.discussions.append(new_disc)

    db.add(new_disc)
    db.commit()
    db.refresh(new_disc)

    return new_disc

def read_disc(db: Session):
    retval = db.query(Discussion).all()
    if retval:
        return retval
    raise HTTPException(status_code=404, detail="No discussions found")


def remove_member_from_topic(db: Session, topic_id: int, user_id: int, current_user_id: int):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    current_admin = db.query(Admin).filter(Admin.user_id == current_user_id).first()
    if not current_admin or current_admin not in topic.admins:
        raise HTTPException(status_code=403, detail="You are not admin of this topic")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user not in topic.members:
        raise HTTPException(status_code=403, detail="User is not a member of this topic")

    topic.members.remove(user)
    db.commit()
    db.refresh(topic)

    return {"message": "Member removed from topic"}


def delete_admin_from_topic(db: Session, topic_id: int, current_user_id: int):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    current_admin = db.query(Admin).filter(Admin.user_id == current_user_id).first()
    if not current_admin or current_admin not in topic.admins:
        raise HTTPException(status_code=403, detail="You are not admin of this topic")

    # if there is only one admin, admin can't delete himself
    if len(topic.admins) == 1:
        raise HTTPException(status_code=400, detail="You cannot leave admin list because this topic has only one admin")

    topic.admins.remove(current_admin)
    db.commit()
    db.refresh(topic)

    return {"message": "You removed yourself from admin list"}


def update_topic(db: Session, topic_id: int, title: str, current_user_id: int):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    current_admin = db.query(Admin).filter(Admin.user_id == current_user_id).first()
    if not current_admin or current_admin not in topic.admins:
        raise HTTPException(status_code=403, detail="You are not admin of this topic")

    topic.title = title
    db.commit()
    db.refresh(topic)

    return topic


def update_discussion(db: Session, topic_id: int, discussion_id: int, name: str, current_user_id: int):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    current_admin = db.query(Admin).filter(Admin.user_id == current_user_id).first()
    if not current_admin or current_admin not in topic.admins:
        raise HTTPException(status_code=403, detail="You are not admin of this topic")

    discussion = db.query(Discussion).filter(Discussion.id == discussion_id).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    if discussion.topic_id != topic_id:
        raise HTTPException(status_code=400, detail="This discussion does not belong to this topic")

    discussion.name = name
    db.commit()
    db.refresh(discussion)
    return discussion

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Not Found")


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