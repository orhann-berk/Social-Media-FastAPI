from pydantic import BaseModel, Field
from db.models import RequestStatus

class UserAuthModel(BaseModel):
    name: str
    password: str
    email: str

class UserUpdateModel(BaseModel):
    name: str
    password: str
    email: str

class PostModel(BaseModel):
    title: str
    image_url: str
    body: str

class UserBaseModel(BaseModel):
    name: str
    email: str

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