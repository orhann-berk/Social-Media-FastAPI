from pydantic import BaseModel, Field

class UserAuthModel(BaseModel):
    name: str
    password: str
    email: str
    is_logged_in: bool = Field(default=False)

class PostModel(BaseModel):
    id: int
    title: str
    image_url: str
    body: str
    class Config:
        from_attributes = True

class UserBaseModel(BaseModel):
    name: str
    email: str