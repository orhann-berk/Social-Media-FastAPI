import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from main import app
from sqlalchemy import create_engine
from db.database import Base, get_db

client = TestClient(app)

#Separate test database
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread":False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

#Override the real DB with the test DB
app.dependency_overrides[get_db] = override_get_db

#This runs before and after EVERY test , wipes the DB clean each time
@pytest.fixture(autouse=True)
def rest_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine) #wipe after test

#Register Helper
def register(username, email):
    return client.post("/register", json={"username": username , "email": email, "password":"password123"} )

#login Helper
def login(username):
    response = client.post("/login", data={"username": username, "password":"password123"})
    return response.json()["access_token"]


def test_register_user():
    response = client.post(
        "/register",
        json={"username":"testuser", "email":"test@test.com" ,"password":"password123"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["username"] == "testuser"

def test_login_user():
    #register first
    client.post("/register", json={"username":"loginuser", "email":"login@test.com", "password":"password123"})
       #login
    response = client.post("/login", data={"username":"loginuser", "password":"password123"})
    assert response.status_code == status.HTTP_200_OK
    assert"access_token" in response.json()

def test_create_post():
    register("post", "post@test.com")
    token = login("post")
    response = client.post("/posts", json={"content":"My first post"}, headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["content"] == "My first post"

def test_create_post_with_image():
    register("imguser", "img@test.com")
    token = login("imguser")
    response = client.post("/posts/", json={"content":"Photo post", "image_url": "http//:image.com/photo.jpg"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["image_url"] == "http//:image.com/photo.jpg"

def test_create_post_unauthorized():
    response = client.post("/posts/", json={"content": "No auth"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_my_wall():
    register("walluser", "wall@test.com")
    token = login("walluser")
    client.post("/posts/", json={"content":"My wall post"},
    headers={"Authorization":f"Bearer {token}"})
    response = client.get("/posts/wall/me", headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

def test_get_my_wall_empty():
    register("emptyuser", "empty@test.com")
    token = login("emptyuser")
    response = client.get("/pots/wall/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_user_wall():
    register("user1", "user@test.com")
    token = login("user1")
    post = client.post("/posts/", json={"content": "User1 post"}, headers={"Authorization":f"Bearer {token}"})
    user_id = post.json()["author"]["id"]
    response = client.get(f"/posts/wall/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

def test_get_user_wall_not_found():
    response = client.get("/posts/wall/0000")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_post():
    register("delete", "delete@test.com")
    token = login("delete")
    post = client.post("/posts/", json={"content":"delete me"}, headers={"Authorization":f"Bearer {token}"})
    post_id = post.json()["id"]
    response = client.delete(f"posts/{post_id}", headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_delete_post_not_found():
    register("delete", "delete@test.com")
    token = login("delete")
    response = client.delete("/posts/0000", headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_other_users_post():
    register("userA", "a@test.com")
    tokenA = login("userA")
    register("userB", "b@test.com")
    tokenB = login("userB")
    post = client.post("/posts/", json={"content": "UserA post"}, headers={"Authorization": f"Bearer {tokenA}"})
    post_id = post.json()["id"]
    response = client.delete(f"/posts/{post_id}", headers={"Authorization":f"Bearer {tokenB}"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_add_comment():
    register("comment", "comment@test.com")
    token = login("comment")
    post = client.post("/posts/", json={"content":"Post to comment on"}, headers={"Authorization":f"Bearer {token}"})
    post_id = post.json()["id"]
    response = client.post(f"/posts/{post_id}/comments", json={"content":"Nice post!"}, headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["content"] == "Nice post!"

def test_add_comment_post_not_found():
    register("comment2", "comment2@test.com")
    token = login("comment2")
    response = client.post("/posts/0000/comment", json={"content": "no comment"}, headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_add_comment_unauthorized():
    response = client.post("/posts/1/comments", json={"content": "No auth comment"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
