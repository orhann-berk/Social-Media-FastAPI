from pydantic import BaseModel
# model is the type of data that goes into the db
class UserAuthModel(BaseModel):
    username: str
    password: str
    email: str