from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class UserAuthModel(BaseModel):
    name: str
    password: str
    email: str
    is_logged_in: bool = Field(default=False)

class PostModel(BaseModel):
    title: str
    image_url: str
    body: str

class UserBaseModel(BaseModel):
    name: str
    email: str
class UserOut (BaseModel):
    id: int
    username: str
    email:EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CommentOut(BaseModel):
    id: int
    content: str
    author: UserOut
    created_at: datetime

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str

class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None

class PostOut(BaseModel):
    id: int
    content: str
    image_url: Optional[str]
    author: UserOut
    created_at: datetime
    comments: List[CommentOut] = []

    class Config:
        from_attributes = True
