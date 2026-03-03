from pydantic import BaseModel, Field

class UserAuthModel(BaseModel):
    name: str
    password: str
    email: str
    is_logged_in: bool = Field(default=False)

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
