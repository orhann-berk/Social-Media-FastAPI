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

# if __name__ == "__main__":
#     # Important: disable reload while debugging
#     uvicorn.run(
#         "main:app",
#         host="127.0.0.1",
#         port=8000,
#         reload=False,
#         log_level="debug",
#     )


# @app.post("/register")
# async def register(user_id: int, user: UserAuthModel):
#     # check if email already exist
#     for u in users:
#         if u["email"] == user.email:
#             raise HTTPException(status_code=409, detail="Email already registered")
#         elif u["username"] == user.username:
#             raise HTTPException(status_code=409, detail="Username already registered")
#     # store the user
#     new_user = {"user_index": user_id, "username": user.username, "email": user.email, "password": user.password, "is_logged_in": user.is_logged_in}
#     users.append(new_user)
#     return {"user_id": user_id, "user": user}
#
# @app.get("/login")
# async def login_user(username: str, password: str):
#     # check loging credentials already exits in pseudo db users list
#     for u in users:
#         if u["username"] == username and u["password"] == password:
#             u["is_logged_in"] = True
#             return {"message": "Login successful"}
#     raise HTTPException(status_code=404, detail="Incorrect username or password")
#
#
# @app.put("/update/{user_id}")
# # updates users credentials
# async def update_user(user_id: int, user: UserAuthModel):
#     update_user_encoded = jsonable_encoder(user)
#     users[user_id] = update_user_encoded
#     return update_user_encoded
#
# # user can see own posts-wall
# @app.get("/users/wall/{user_id}")
# async def get_user_posts(user_id: int):
#     for u in users:
#         if u["user_index"] == user_id:
#             if u["is_logged_in"] == True:
#                 return {"message": "Wall posts successfully fetched", "posts": user_posts}
#             else:
#                 return {"message": "Please login to see posts"}
#         else:
#             raise HTTPException(status_code=404, detail="User profile not found")
#     return None
#
# # user can add posts
# @app.post("/users/{user_id}/posts")
# async def create_user_post(user_id: int, post_id:int, post: PostModel):
#     if users[user_id]["is_logged_in"]:
#         post.post_id = post_id
#         new_post = {"post_id": post_id, "title": post.title ,"image": post.image, "description": post.description}
#         user_posts.append(new_post)
#     return {"user_id": user_id, "post_id": post_id, "post": post}
#
# # user can update posts
# @app.put("/update/{user_id}/posts/{post_id}")
# # updates users credentials
# async def update_post(post_id: int, post: PostModel):
#     update_user_encoded = jsonable_encoder(post)
#     users[post_id] = update_user_encoded
#     return update_user_encoded