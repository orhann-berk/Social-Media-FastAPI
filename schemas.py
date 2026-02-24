from pydantic import BaseModel, Field

class UserAuthModel(BaseModel):
    username: str
    password: str
    email: str

class PostModel(BaseModel):
    post_id: int
    title: str
    image: str
    body: str

class UserBaseModel(BaseModel):
    username: str
    email: str
