from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base

# Association table to connect admins and topics
topics_admins = Table('topic_admins', Base.metadata,
Column('admin_id', Integer, ForeignKey('admins.id')),
Column('topic_id', Integer, ForeignKey('topics.id'))
)


# Association table to connect members and topics
topics_members = Table('topic_members', Base.metadata,
Column('member_id', Integer, ForeignKey('users.id')),
Column('topic_id', Integer, ForeignKey('topics.id'))
)



# unique-pk is handling by database itself
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    topics = relationship("Topic", secondary=topics_members, back_populates="members")
    admin = relationship("Admin", back_populates="user", uselist=False)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    discussions = relationship("Discussion", back_populates="topic")
    admins = relationship("Admin", secondary=topics_admins, back_populates="topics")
    members = relationship("User", secondary=topics_members, back_populates="topics")


class Discussion(Base):
    __tablename__ = "discussions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    topic = relationship("Topic", back_populates="discussions")


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    topics = relationship("Topic", secondary=topics_admins, back_populates="admins")
    user = relationship("User", back_populates="admin")

