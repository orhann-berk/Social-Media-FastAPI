import uvicorn
from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session
from schemas import UserAuthModel, UserBaseModel
import crud
from database import get_db

app = FastAPI()

# python list for use of db
@app.get("/users") # , response_model = list[UserBaseModel]
def get_users(db: Session = Depends(get_db)):
    result = crud.read_users(db)
    return result


@app.post("/users", status_code=status.HTTP_201_CREATED)
def add_user(user: UserAuthModel, db: Session = Depends(get_db)):
    return crud.add_user(db, name=user.username, email=user.email)

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return crud.delete_user(db, user_id = user_id)

if __name__ == "__main__":
    # Important: disable reload while debugging
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="debug",
    )