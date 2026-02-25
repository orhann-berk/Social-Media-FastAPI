from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///../social.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    # open the db session
    db = SessionLocal()
    try:
        # open the db
        yield db
    finally:
        # close the db
        db.close()

Base.metadata.create_all(bind=engine)