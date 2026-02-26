from pydantic import BaseModel, Field

class UserAuthModel(BaseModel):
    name: str
    password: str
    email: str
    is_logged_in: bool = Field(default=False)
class UserBaseModel(BaseModel):
    name: str
    email: str

class PostCreate(BaseModel): #create post
    title: str
    image_url: str
    body: str
    user_id: int

class PostOut(PostCreate): #returns post
    id: int
    class Config:
        from_attributes = True

