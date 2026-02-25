from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# unique-pk is handling by database itself
class DbUser(Base):
    __tablename__ = "allusers"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

# class DbPost(Base):
#     __tablename__ = "allposts"
#     post_id = Column(Integer, primary_key=True)
#     poster_id = Column(Integer, foreign_key="allusers.id")
#     title = Column(String)
#     body = Column(String)
#     image_url = Column(String)