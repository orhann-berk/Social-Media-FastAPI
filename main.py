import uvicorn
from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session
from schemas import UserAuthModel, PostModel
import crud
from db.database import get_db

app = FastAPI()

# USER ADD, UPDATE, DELETE AND GET OPERATIONS.
@app.get("/users/all") # , response_model = List[UserBaseModel]
def get_users(db: Session = Depends(get_db)):
    result = crud.read_users(db)
    return result

@app.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user(db, user_id = user_id)


@app.post("/register", status_code=status.HTTP_201_CREATED)
def add_user(user: UserAuthModel, db: Session = Depends(get_db)):
    return crud.add_user(db, name=user.name, email=user.email, password = user.password, is_logged_in = user.is_logged_in)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return crud.delete_user(db, user_id = user_id)


@app.put("/users/{user_id}", status_code=status.HTTP_202_ACCEPTED)
def update_user(user: UserAuthModel, user_id:int, db: Session = Depends(get_db)):
    return crud.update_user(db, user_id= user_id, name = user.name, email = user.email, password=user.password)


@app.post("/add/post", status_code=status.HTTP_202_ACCEPTED)
def add_post(post: PostModel, db: Session = Depends(get_db)):
    return crud.add_post(db, title = post.title, body = post.body, image_url= post.image_url)


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    result = crud.read_posts(db)
    return result


# Login
@app.get("/login")
def login_user(name: str, password: str, db: Session = Depends(get_db)):
    return crud.login_user(db, name = name, password = password)

#Log-out#
@app.get("/logout")
def logout_user(name: str, password: str, db: Session = Depends(get_db)):
    return crud.logout_user(db, name = name, password = password)

if __name__ == "__main__":
    # Important: disable reload while debugging
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )

