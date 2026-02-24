from pydantic import BaseModel, Field
# model is the type of data that goes into the db
class UserAuthModel(BaseModel):
    username: str
    password: str
    email: str
    is_logged_in: bool = Field(default=False)