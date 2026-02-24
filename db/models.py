from pydantic import BaseModel, Field
# model is the type of data that goes into the db
# user model for auth operations login/register/update
class UserAuthModel(BaseModel):
    username: str
    password: str
    email: str
    is_logged_in: bool = Field(default=False)

class PostModel(BaseModel):
    post_id: int
    title: str
    image: str
    description: str
