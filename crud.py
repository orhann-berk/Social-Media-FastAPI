from sqlalchemy.orm import Session
from models import DbUser, DbPost

def read_users(db: Session):
    retval = db.query(DbUser).all()
    return retval

def post_user(db: Session, name:str, email:str, password:str):
    user = DbUser(name = name, email = email, password = password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(DbUser).filter(DbUser.id == user_id).first()
    db.delete(user)
    db.commit()
    return

def add_post(db: Session, title: str, body: str, image_url: str):
    post = DbPost(title= title, body= body, image_url = image_url)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def update_user(db: Session, user_id: int, name: str, email: str, password: str):
    db_user = db.query(DbUser).filter(DbUser.id == user_id).first()
    db_user.name = name
    db_user.email = email
    db_user.password = password
    db.commit()
    return