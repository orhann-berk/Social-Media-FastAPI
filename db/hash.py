from passlib.context import CryptContext

pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Hash:

    @staticmethod
    def bcrypt(password: str):
        return pwd_cxt.hash(password[:72])

    @staticmethod
    def verify(hashed_password, plain_password):
        return pwd_cxt.verify(plain_password[:72], hashed_password)
