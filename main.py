import uvicorn
from typing import List
from fastapi import HTTPException, FastAPI, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schemas import UserAuthModel, UserBaseModel
import crud
from db.database import get_db, engine, Base
from Posts import router as posts_router
from db.hash import Hash
from oauth2 import get_current_user, create_access_token
from db import models

app = FastAPI()
app.include_router(posts_router)

Base.metadata.create_all(bind=engine)


@app.get("/users/all", response_model=List[UserBaseModel], tags=["users"])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = crud.read_users(db)
    return result


@app.get("/user/{user_id}", tags=["users"])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

        return crud.get_user(db, user_id=user_id)


@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["register"])
def add_user(user: UserAuthModel, db: Session = Depends(get_db)):
    return crud.add_user(
        db,
        name=user.username,
        email=user.email,
        password=user.password,
    )


@app.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(),
               db: Session = Depends(get_db)):

    user = crud.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(
        data={"sub": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/logout", tags=["login/logout"])
def logout_user(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {"message": "Logged out successfully"}


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["user/delete"])
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.delete_user(db, user_id=user_id)


@app.put("/users/{user_id}", status_code=status.HTTP_202_ACCEPTED, tags=["user/update"])
def update_user(
    user: UserAuthModel,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.update_user(
        db,
        user_id=user_id,
        name=user.username,
        email=user.email,
        password=user.password
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )
