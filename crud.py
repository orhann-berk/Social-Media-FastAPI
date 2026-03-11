from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import current_user
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