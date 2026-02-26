from sqlalchemy.orm import Session
from db.models import DbUser, DbPost


def read_users(db: Session):
    retval = db.query(DbUser).all()
    return retval


def get_user(db: Session, user_id: int):
    retval = db.query(DbUser).filter(DbUser.id == user_id).first()
    return retval


def add_user(db: Session, name:str, email:str, password:str, is_logged_in: bool):
    user = DbUser(name = name, email = email, password = password, is_logged_in = is_logged_in)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    db.delete(user)
    db.commit()
    return


def update_user(db: Session, user_id: int, name: str, email: str, password: str):
    db_user = db.query(DbUser).filter(DbUser.id == user_id).first()
    db_user.name = name
    db_user.email = email
    db_user.password = password
    db.commit()
    return


def login_user(db: Session, name: str, password: str):
    matching_user = db.query(DbUser).filter(DbUser.name == name, DbUser.password == password).first()
    if matching_user:
        matching_user.is_logged_in = True
        db.commit()
        return matching_user
    else:
        return "Wrong username or password"


def add_post(db: Session, title: str, body: str, image_url: str, user_id: int):
    post = DbPost(title = title, body = body, image_url = image_url, user_id=user_id) #to link post to the user
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def read_posts(db:Session): #reads all posts
    query = db.query(DbPost).all()
    return query

#Find the post whose id equals post_id, and give me the first result, Stops querying after the first match
def read_post(db: Session, post_id: int):
    return db.query(DbPost).filter(DbPost.id == post_id).first()
