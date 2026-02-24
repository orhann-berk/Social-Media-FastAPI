from pydantic import BaseModel
# model is the type of data that goes into the db
class UserAuthModel(BaseModel):
    user_id: int
    username: str
    password: str
    email: str
    is_logged_in: bool
class LoginUser(BaseModel):
    username: str
    password: str