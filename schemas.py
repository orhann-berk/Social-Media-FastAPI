from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str


class UserAuthModel(BaseModel):
    name: str
    password: str
    email: str
    is_logged_in: bool = Field(default=False)

class UserOut (BaseModel):
    id: int
    username: str
    email:EmailStr
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PostModel(BaseModel):
    title: str
    image_url: str
    body: str

class UserBaseModel(BaseModel):
    name: str
    email: str

class CommentCreate(BaseModel):
    content: str

class CommentOut(BaseModel):
    id: int
    content: str
    author: UserOut
    created_at: datetime

    class Config:
        from_attributes = True

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
