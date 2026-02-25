from pydantic import BaseModel, Field

class UserAuthModel(BaseModel):
    name: str
    password: str
    email: str

class PostModel(BaseModel):
    post_id: int
    title: str
    image_url: str
    body: str

class UserBaseModel(BaseModel):
    name: str
    email: str
