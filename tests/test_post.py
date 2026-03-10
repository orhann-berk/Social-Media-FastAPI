import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette import status

from main import app
from db.database import Base, get_db

# ─── Test Database Setup ──────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ─── Helper Functions ─────────────────────────────────────────────────────────

def register_and_login(username="testuser", email="test@test.com", password="testpass123"):
    #Register a user and return their token
    response = client.post("/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    response = client.post("/login",
        data={"username": username, "password": password}
    )
    resp = response.json()
    token = resp["access_token"]
    return token

def auth_headers(token):
    #Return Authorization header dict
    return {"Authorization": f"Bearer {token}"}


def create_post(token, content="Test post", image_url=None):
    #Helper to create a post and return the response
    return client.post(
        "/posts/",
        json={"content": content, "image_url": image_url},
        headers=auth_headers(token)
    )


# ─── Create Post Tests ────────────────────────────────────────────────────────

def test_create_post_success():
    token = register_and_login()
    response = create_post(token, content="Hello world")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["content"] == "Hello world"
    assert response.json()["image_url"] is None
    assert "id" in response.json()
    assert "author" in response.json()
    assert "created_at" in response.json()


def test_create_post_with_image():
    token = register_and_login()
    response = create_post(token, content="Post with image", image_url="http://img.com/photo.jpg")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["image_url"] == "http://img.com/photo.jpg"


def test_create_post_unauthorized():
    #Should fail with no token
    response = client.post("/posts/",
        json={"content": "No token post"}
    )
    assert response.status_code == 401


def test_create_post_missing_content():
    #Should fail with missing required field
    token = register_and_login()
    response = client.post("/posts/",
        json={},   # content is required
        headers=auth_headers(token)
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT   # Pydantic validation error


# ─── Get My Wall Tests ────────────────────────────────────────────────────────

def test_get_my_wall_empty():
    #Wall should be empty for new user
    token = register_and_login()
    response = client.get("/posts/wall/me", headers=auth_headers(token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_my_wall_with_posts():
    #Wall should return only the current user's posts
    token = register_and_login()
    create_post(token, content="First post")
    time.sleep(1)
    create_post(token, content="Second post")

    response = client.get("/posts/wall/me", headers=auth_headers(token))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    # Newest first
    assert response.json()[0]["content"] == "Second post"
    assert response.json()[1]["content"] == "First post"


def test_get_my_wall_only_my_posts():
    #Wall should NOT include other users' posts
    token1 = register_and_login("user1", "user1@test.com", "pass123")
    token2 = register_and_login("user2", "user2@test.com", "pass123")

    create_post(token1, content="User1 post")
    create_post(token2, content="User2 post")

    response = client.get("/posts/wall/me", headers=auth_headers(token1))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["content"] == "User1 post"


def test_get_my_wall_unauthorized():
    response = client.get("/posts/wall/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Get User Wall Tests ──────────────────────────────────────────────────────

def test_get_user_wall_success():
    #Should return another user's posts publicly
    token = register_and_login()
    create_post(token, content="Public post")

    # Get the user id from the post response
    post_response = create_post(token, content="Another post")
    user_id = post_response.json()["author"]["id"]

    response = client.get(f"/posts/wall/{user_id}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


def test_get_user_wall_not_found():
    #Should return 404 for non-existent user
    response = client.get("/posts/wall/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_get_user_wall_empty():
    #Should return empty list for user with no posts
    token = register_and_login()
    # Get user id without creating posts
    login_response = client.post("/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    # Register gives us no id directly, so create and delete a post
    post = create_post(token, "temp")
    user_id = post.json()["author"]["id"]

    # Delete it
    post_id = post.json()["id"]
    client.delete(f"/posts/{post_id}", headers=auth_headers(token))

    response = client.get(f"/posts/wall/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


# ─── Delete Post Tests ────────────────────────────────────────────────────────

def test_delete_post_success():
    token = register_and_login()
    post = create_post(token, content="To be deleted")
    post_id = post.json()["id"]

    response = client.delete(f"/posts/{post_id}", headers=auth_headers(token))

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Confirm it's gone from wall
    wall = client.get("/posts/wall/me", headers=auth_headers(token))
    assert len(wall.json()) == 0


def test_delete_post_not_found():
    token = register_and_login()
    response = client.delete("/posts/9999", headers=auth_headers(token))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_delete_post_not_authorized():
    #User should not be able to delete another user's post
    token1 = register_and_login("user1", "user1@test.com", "pass123")
    token2 = register_and_login("user2", "user2@test.com", "pass123")

    post = create_post(token1, content="User1 post")
    post_id = post.json()["id"]

    # user2 tries to delete user1's post
    response = client.delete(f"/posts/{post_id}", headers=auth_headers(token2))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authorized"


def test_delete_post_unauthorized():
    token = register_and_login()
    post = create_post(token)
    post_id = post.json()["id"]

    response = client.delete(f"/posts/{post_id}")  # no token
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Comment Tests ────────────────────────────────────────────────────────────

def test_add_comment_success():
    token = register_and_login()
    post = create_post(token, content="Post to comment on")
    post_id = post.json()["id"]

    response = client.post(
        f"/posts/{post_id}/comments",
        json={"content": "Great post!"},
        headers=auth_headers(token)
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["content"] == "Great post!"
    assert "author" in response.json()
    assert "created_at" in response.json()


def test_add_comment_post_not_found():
    token = register_and_login()
    response = client.post(
        "/posts/9999/comments",
        json={"content": "Comment on nothing"},
        headers=auth_headers(token)
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_add_comment_unauthorized():
    token = register_and_login()
    post = create_post(token)
    post_id = post.json()["id"]

    response = client.post(
        f"/posts/{post_id}/comments",
        json={"content": "No token comment"}
        # no headers
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_comment_another_user():
    #A different user should be able to comment on someone's post
    token1 = register_and_login("user1", "user1@test.com", "pass123")
    token2 = register_and_login("user2", "user2@test.com", "pass123")

    post = create_post(token1, content="User1 post")
    post_id = post.json()["id"]

    # user2 comments on user1's post — this should be allowed
    response = client.post(
        f"/posts/{post_id}/comments",
        json={"content": "Comment from user2"},
        headers=auth_headers(token2)
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["author"]["username"] == "user2"