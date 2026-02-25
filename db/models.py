from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy import ForeignKey

Base = declarative_base()

# unique-pk is handling by database itself
class DbUser(Base):
    __tablename__ = "allusers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    is_logged_in = Column(Boolean)

class DbPost(Base):
    __tablename__ = "allposts"
    id = Column(Integer, primary_key=True, index=True)
#   poster_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    body = Column(String)
    image_url = Column(String)
    user_id = Column(Integer, ForeignKey("allusers.id"))  # NEW
