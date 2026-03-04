from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from db.models import DbUser, DbPost, DbFriendRequest, RequestStatus


def read_users(db: Session):
    retval = db.query(DbUser).all()
    return retval

def get_user(db: Session, user_id: int):
    retval = db.query(DbUser).filter(DbUser.id == user_id).first()
    if retval:
        return retval
    return  "User not found"


def add_user(db: Session, name:str, email:str, password:str):
    user = DbUser(name = name, email = email, password = password, is_logged_in = False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if not user:
        return "User not found"
    elif user.is_logged_in:
        db.delete(user)
        db.commit()
        return "User deleted"
    else:
        return "User must login"


def update_user(db: Session, user_id: int, name: str, email: str, password: str):
    db_user = db.query(DbUser).filter(DbUser.id == user_id).first()
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


def login_user(db: Session, name: str, password: str):
    matching_user = db.query(DbUser).filter(DbUser.name == name and DbUser.password == password).first()
    if matching_user:
        matching_user.is_logged_in = True
        db.commit()
        return "Login successful"
    else:
        return "Login unsuccessful"


def add_post(db: Session, title: str, body: str, image_url: str):
    post = DbPost(title = title, body = body, image_url = image_url)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def read_posts(db:Session):
    retval = db.query(DbPost).all()
    return retval


def logout_user(db: Session, name: str, password: str):
    user_out = db.query(DbUser).filter(DbUser.name == name and DbUser.password == password).first()
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

def create_friend_request(db: Session, sender_id: int, receiver_id: int):
    if sender_id == receiver_id:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="You can not send a friend request to yourself.")

    receiver = db.query(DbUser).filter(DbUser.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Receiver does not exist.")

    existing_request = db.query(DbFriendRequest).filter(DbFriendRequest.sender_id == sender_id,
                                                        DbFriendRequest.receiver_id == receiver_id).first()

    if existing_request:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="You have already sent a friend.")

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