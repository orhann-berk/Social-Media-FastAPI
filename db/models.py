from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

# unique-pk is handling by database itself
class DbUser(Base):
    __tablename__ = "allusers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    is_logged_in = Column(Boolean, default=False)

class DbPost(Base):
    __tablename__ = "allposts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    body = Column(String)
    image_url = Column(String)

class RequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class DbFriendRequest(Base):
    __tablename__ = "friend_requests"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("allusers.id"))
    receiver_id = Column(Integer, ForeignKey("allusers.id"))
    status = Column(SQLEnum(RequestStatus))
    default = RequestStatus.pending

    sender = relationship("DbUser", foreign_keys=[sender_id])
    receiver = relationship("DbUser", foreign_keys=[receiver_id])