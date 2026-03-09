from passlib.context import CryptContext

pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)

class Hash:

    @staticmethod
    def bcrypt(password: str):
        return pwd_cxt.hash(password)

    @staticmethod
    def verify(plain_password, hashed_password):
        return pwd_cxt.verify(plain_password, hashed_password)
