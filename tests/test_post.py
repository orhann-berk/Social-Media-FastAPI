import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

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

def test_register_user():
    response = client.post(
        "/register",
        json={"username":"testuser", "email":"test@test.com" ,"password":"password123"})
    assert response.status_code == HTTP_201_CREATED
    assert response.json()["username"] == "testuser"

def test_login_user():
    #register first
    client.post("/register", json={"username":"loginuser", "email":"login@test.com", "password":"password123"})
       #login
    response = client.post("/login", data={"username":"loginuser", "password":"password123"})
    assert response.status_code == HTTP_200_OK
    assert"access_token" in response.json()

def test_create_post():
    #register
    client.post("/register", json={"username":"post", "email":"post@test.com" ,"password":"password123"})
    #login
    login = client.post("/login", data = {"username":"post", "password":"password123"})
    token = login.json()["access_token"]
    #create post
    response = client.post("/posts", json={"content":"My first post"}, headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == HTTP_201_CREATED
    assert response.json()["content"] == "My first post"

def test_get_my_wall():
    #register
    client.post("/register", json={"username":"walluser", "email":"wall@test.com", "password":"password123"})
    #login
    login = client.post("/login", data={"username":"walluser","password":"password123"})
    token = login.json()["access_token"]
    #create post
    client.post("/posts/", json={"content":"Wall post"},
    headers={"Authorization":f"Bearer {token}"})
    #get wall
    response = client.get("/posts/wall/me", headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 1

def test_delete_post():
    #register
    client.post("/register", json={"username":"deleteuser", "email":"delete@test.com", "password":"password123"})
    #login
    login = client.post("/login", data={"username":"deleteuser", "password":"password123"})
    token = login.json()["access_token"]
    #create post
    post = client.post("/posts/", json={"content":"Delete me"}, headers={"Authorization":f"Bearer {token}"})
    post_id = post.json()["id"]
    #delete post
    response = client.delete(f"posts/{post_id}", headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == HTTP_204_NO_CONTENT

def test_add_comment():
    #register
    client.post("/register", json={"username": "commentuser", "email":"comment@test.com", "password":"password123"})
    #login
    login =  client.post("/login", data={"username":"commentuser", "password":"password123"})
    token = login.json()["access_token"]
    #create post
    post = client.post("/posts/", json={"content":"Post to comment on"}, headers={"Authorization":f"Bearer {token}"})
    post_id = post.json()["id"]
    #comment
    response = client.post(f"/posts/{post_id}/comments", json={"content":"Nice post!"}, headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == HTTP_201_CREATED
    assert response.json()["content"] == "Nice post!"