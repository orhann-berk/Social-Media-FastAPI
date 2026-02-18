from pydantic.v1 import BaseModel

class UserAuthModel(BaseModel):
    username: str
    password: str
    email: str
