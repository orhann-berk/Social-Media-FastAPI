from pydantic import EmailStr
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from db.models import RequestStatus

class UserBaseModel(BaseModel):
    username: str
    email: str

class UserAuthModel(BaseModel):
    username: str
    email: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserOut (BaseModel):
    id: int
    username: str
    email:EmailStr
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None


class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: int
    content: str
    author: UserOut
    created_at: datetime

    class Config:
        from_attributes = True


class PostOut(BaseModel):
    id: int
    content: str
    image_url: Optional[str]
    author: UserOut
    created_at: datetime
    comments: List[CommentOut] = []

    class Config:
        from_attributes = True


class TopicModel(BaseModel):
    title: str
    discussions: List[DiscussionModel] = []
    admins: List[AdminAll] = []
    members: List[UserOut] = []

class AdminAll(BaseModel):
    id: int
    user_id: int
    name: str

class AddTopicModel(BaseModel):
    title: str

class DiscussionModel(BaseModel):
    name: str

class AddMemberModel(BaseModel):
    user_id: int

class AddAdminModel(BaseModel):
    user_id: int

class UpdateTopicModel(BaseModel):
    title: str

class UpdateDiscussionModel(BaseModel):
    name: str

class FriendRequestCreate(BaseModel):
    sender_id: int
    receiver_id: int

class FriendRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: RequestStatus

    class Config:
        from_attributes = True