import pytest
from sqlalchemy.orm import sessionmaker
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_422_UNPROCESSABLE_CONTENT, \
    HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST
from starlette.testclient import TestClient

from main import app
from sqlalchemy import create_engine
from db.database import Base, get_db

client: TestClient = TestClient(app)

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


def test_add_topic():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    response = client.post("/topics/add", json={"title": "space"}, headers={"Authorization": f"Bearer {token}"})
    response_validation_error = client.post("/topics/add", json={"titlsdae": "ssadfpace"}, headers={"Authorization": f"Bearer {token}"})
    response_check_admin = client.get("/topics/1", headers={"Authorization": f"Bearer {token}"} )
    assert response_validation_error.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert response.status_code == HTTP_201_CREATED
    assert response.json()["title"] == "space"
    assert response_check_admin.status_code == HTTP_200_OK
    assert response_check_admin.json()["admins"][0]["name"] == "a"


def test_check_topic_id():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    response_create_topic = client.post("/topics/add", json={"title": "space"}, headers={"Authorization": f"Bearer {token}"})
    response_true = client.get("/topics/1", headers={"Authorization": f"Bearer {token}"})
    response_false = client.get("/topics/123", headers={"Authorization": f"Bearer {token}"})
    assert response_false.status_code == HTTP_404_NOT_FOUND
    assert response_false.json()["detail"] == "Topic not found"
    assert response_create_topic.status_code == HTTP_201_CREATED
    assert response_true.json()["title"] == "space"


def test_update_topic():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    client.post("/register", json={"username": "b", "email": "b@email.com", "password": "b"})
    # login
    login_admin = client.post("/login", data={"username": "a", "password": "a"})
    token_admin = login_admin.json()["access_token"]
    login = client.post("/login", data={"username": "b", "password": "b"})
    token = login.json()["access_token"]
    response_create_topic = client.post("/topics/add", json={"title": "space"},
                                        headers={"Authorization": f"Bearer {token_admin}"})
    response_true = client.put("/topics/1", json={"title":"space2"}, headers={"Authorization": f"Bearer {token_admin}"})
    response_false_not_admin = client.put("/topics/1", json={"title":"space2"}, headers={"Authorization": f"Bearer {token}"})
    response_false_not_topic = client.put("/topics/123", json={"title":"space2"}, headers={"Authorization": f"Bearer {token_admin}"})
    response_false_typing = client.put("/topics/1", json={"titlsdfae":"space2"}, headers={"Authorization": f"Bearer {token_admin}"})
    assert response_false_not_topic.status_code == HTTP_404_NOT_FOUND
    assert response_false_not_topic.json()["detail"] == "Topic not found"
    assert response_false_not_admin.status_code == HTTP_403_FORBIDDEN
    assert response_false_not_admin.json()["detail"] == "You are not admin of this topic"
    assert response_true.status_code == HTTP_200_OK
    assert response_true.json()["title"] == "space2"
    assert response_false_typing.status_code == HTTP_422_UNPROCESSABLE_CONTENT

def test_add_discussion_topic():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    response_create_topic = client.post("/topics/add", json={"title": "space"},
                                        headers={"Authorization": f"Bearer {token}"})
    response_false_not_member = client.post("/topics/1/discussion", json={"name":"stars"}, headers={"Authorization": f"Bearer {token}"})
    assert response_false_not_member.status_code == HTTP_403_FORBIDDEN
    assert response_false_not_member.json()["detail"] == "Only members can add discussion"
    response_true_member = client.post("/topics/1/add-member", json={"user_id":"1"}, headers={"Authorization": f"Bearer {token}"})
    assert response_true_member.status_code == HTTP_201_CREATED
    assert response_true_member.json()["id"] == 1
    response_true_member_add_discussion = client.post("/topics/1/discussion", json={"name":"stars"}, headers={"Authorization": f"Bearer {token}"})
    assert response_true_member_add_discussion.status_code == HTTP_201_CREATED
    assert response_true_member_add_discussion.json()["id"] == 1
    response_false_topic_not_found = client.post("/topics/132/discussion", json={"name":"stars"}, headers={"Authorization": f"Bearer {token}"})
    assert response_false_topic_not_found.status_code == HTTP_404_NOT_FOUND
    assert response_false_topic_not_found.json()["detail"] == "Topic not found"

def test_get_all_discussions():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    response_create_topic = client.post("/topics/add", json={"title": "space"},
                                        headers={"Authorization": f"Bearer {token}"})
    response_true_member = client.post("/topics/1/add-member", json={"user_id": "1"},
                                       headers={"Authorization": f"Bearer {token}"})
    response_false_no_discussion = client.get("/discussion/all", headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_discussion.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_discussion.json()["detail"] == "No discussions found"
    response_true_member_add_discussion = client.post("/topics/1/discussion", json={"name": "stars"},
                                                      headers={"Authorization": f"Bearer {token}"})
    response_get_discussions_true = client.get("/discussion/all", headers={"Authorization": f"Bearer {token}"})
    assert response_get_discussions_true.status_code == HTTP_200_OK
    assert response_get_discussions_true.json()[0]["name"] == "stars"


def test_add_admin_to_topic():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    client.post("/register", json={"username": "b", "email": "b@email.com", "password": "b"})
    client.post("/register", json={"username": "c", "email": "c@email.com", "password": "c"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    response_create_topic = client.post("/topics/add", json={"title": "space"},
                                        headers={"Authorization": f"Bearer {token}"})
    response_true_member = client.post("/topics/1/add-member", json={"user_id": "1"},
                                       headers={"Authorization": f"Bearer {token}"})
    response_false_no_topic = client.post("/topics/123/add-admin", json={"user_id": "0"}, headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_topic.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_topic.json()["detail"] == "Topic not found"
    response_false_no_user = client.post("/topics/1/add-admin", json={"user_id": "10"}, headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_user.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_user.json()["detail"] == "User not found"
    login_false = client.post("/login", data={"username": "b", "password": "b"})
    token_false = login_false.json()["access_token"]
    response_false_not_admin = client.post("/topics/1/add-admin", json={"user_id": "3"}, headers={"Authorization": f"Bearer {token_false}"})
    assert response_false_not_admin.status_code == HTTP_403_FORBIDDEN
    assert response_false_not_admin.json()["detail"] == "You are not admin of this topic"
    response_true = client.post("/topics/1/add-admin", json={"user_id": "3"}, headers={"Authorization": f"Bearer {token}"})
    assert response_true.status_code == HTTP_201_CREATED
    assert response_true.json()["title"] == "space"

def test_add_member_to_topic():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    client.post("/register", json={"username": "b", "email": "b@email.com", "password": "b"})
    client.post("/register", json={"username": "c", "email": "c@email.com", "password": "c"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    response_create_topic = client.post("/topics/add", json={"title": "space"},
                                        headers={"Authorization": f"Bearer {token}"})
    response_false_add_member_no_topic = client.post("/topics/123/add-member", json={"user_id": "1"},
                                       headers={"Authorization": f"Bearer {token}"})
    assert response_false_add_member_no_topic.status_code == HTTP_404_NOT_FOUND
    assert response_false_add_member_no_topic.json()["detail"] == "Topic not found"

    response_false_no_user_id = client.post("/topics/1/add-member", json={"user_id": "112"},
                                       headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_user_id.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_user_id.json()["detail"] == "User not found"
    login_false = client.post("/login", data={"username": "b", "password": "b"})
    token_false = login_false.json()["access_token"]
    response_false_not_admin = client.post("/topics/1/add-member", json={"user_id": "3"},
                                       headers={"Authorization": f"Bearer {token_false}"})
    assert response_false_not_admin.status_code == HTTP_403_FORBIDDEN
    assert response_false_not_admin.json()["detail"] == "You are not admin of this topic"

    response_true = client.post("/topics/1/add-member", json={"user_id": "3"}, headers={"Authorization": f"Bearer {token}"})
    assert response_true.status_code == HTTP_201_CREATED
    assert response_true.json()["title"] == "space"

def test_update_topic_discussion():
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    client.post("/register", json={"username": "b", "email": "b@email.com", "password": "b"})
    client.post("/register", json={"username": "c", "email": "c@email.com", "password": "c"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    client.post("/topics/add", json={"title": "space"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/topics/1/discussion", json={"name": "stars"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/topics/1/discussion", json={"name": "galaxy"}, headers={"Authorization": f"Bearer {token}"})

    response_false_not_topic = client.put("/topics/123/discussions/1", json={"name": "starks"}, headers={"Authorization": f"Bearer {token}"})
    assert response_false_not_topic.status_code == HTTP_404_NOT_FOUND
    assert response_false_not_topic.json()["detail"] == "Topic not found"

    login_false = client.post("/login", data={"username": "b", "password": "b"})
    token_false = login_false.json()["access_token"]
    response_false_not_admin = client.put("/topics/1/discussions/1", json={"name": "starks"}, headers={"Authorization": f"Bearer {token_false}"})
    assert response_false_not_admin.status_code == HTTP_403_FORBIDDEN
    assert response_false_not_admin.json()["detail"] == "You are not admin of this topic"

    response_false_disc_not = client.put("/topics/1/discussions/123", json={"name": "starks"}, headers={"Authorization": f"Bearer {token}"})
    assert response_false_disc_not.status_code == HTTP_404_NOT_FOUND
    assert response_false_disc_not.json()["detail"] == "Discussion not found"

def test_remove_member_from_topic():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    client.post("/register", json={"username": "b", "email": "b@email.com", "password": "b"})
    client.post("/register", json={"username": "c", "email": "c@email.com", "password": "c"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    client.post("/topics/add", json={"title": "space"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/topics/1/add-member", json={"user_id": "3"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/topics/1/add-member", json={"user_id": "1"}, headers={"Authorization": f"Bearer {token}"})

    response_false_no_topic = client.delete("/topics/123/members/3", headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_topic.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_topic.json()["detail"] == "Topic not found"

    response_false_no_user = client.delete("/topics/1/members/100", headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_user.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_user.json()["detail"] == "User not found"

    response_false_not_member = client.delete("/topics/1/members/2", headers={"Authorization": f"Bearer {token}"})
    assert response_false_not_member.status_code == HTTP_403_FORBIDDEN
    assert response_false_not_member.json()["detail"] == "User is not a member of this topic"

    response_check_admin = client.get("/topics/1", headers={"Authorization": f"Bearer {token}"})
    assert response_check_admin.json()["admins"][0]["name"] == "a"

    response_true_member = client.delete("/topics/1/members/1", headers={"Authorization": f"Bearer {token}"})
    assert response_true_member.status_code == HTTP_200_OK
    assert response_true_member.json()["message"] == "Member removed from topic"

def test_delete_admin_topic():
    # register
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    client.post("/register", json={"username": "b", "email": "b@email.com", "password": "b"})
    client.post("/register", json={"username": "c", "email": "c@email.com", "password": "c"})
    # login
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    client.post("/topics/add", json={"title": "space"}, headers={"Authorization": f"Bearer {token}"})

    response_false_no_topic = client.delete("topics/10/delete-admin", headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_topic.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_topic.json()["detail"] == "Topic not found"

    login_false = client.post("/login", data={"username": "b", "password": "b"})
    token_false = login_false.json()["access_token"]
    response_false_not_admin = client.delete("topics/1/delete-admin", headers={"Authorization": f"Bearer {token_false}"})
    assert response_false_not_admin.status_code == HTTP_403_FORBIDDEN
    assert response_false_not_admin.json()["detail"] == "You are not admin of this topic"

    response_false_only_admin = client.delete("topics/1/delete-admin", headers={"Authorization": f"Bearer {token}"})
    assert response_false_only_admin.status_code == HTTP_400_BAD_REQUEST
    assert response_false_only_admin.json()["detail"] == "You cannot leave admin list because this topic has only one admin"

    client.post("/topics/1/add-admin", json={"user_id": "3"}, headers={"Authorization": f"Bearer {token}"})
    response_true = client.delete("topics/1/delete-admin", headers={"Authorization": f"Bearer {token}"})
    assert response_true.status_code == HTTP_200_OK
    assert response_true.json()["message"] == "You removed yourself from admin list"

def test_delete_topic():
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    client.post("/register", json={"username": "b", "email": "b@email.com", "password": "b"})
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    client.post("/topics/add", json={"title": "space"}, headers={"Authorization": f"Bearer {token}"})
    response_false_no_topic = client.delete("/topics/delete/10", headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_topic.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_topic.json()["detail"] == "Topic not found"

    login_false = client.post("/login", data={"username": "b", "password": "b"})
    token_false = login_false.json()["access_token"]

    response_false_only_admin = client.delete("/topics/delete/1", headers={"Authorization": f"Bearer {token_false}"})
    assert response_false_only_admin.status_code == HTTP_403_FORBIDDEN
    assert response_false_only_admin.json()["detail"] == "You have to be admin for delete topic"

    response_true = client.delete("/topics/delete/1", headers={"Authorization": f"Bearer {token}"})
    assert response_true.status_code == HTTP_200_OK
    assert response_true.json()["message"] == "Topic has been deleted"

def test_delete_discussion():
    client.post("/register", json={"username": "a", "email": "a@email.com", "password": "a"})
    client.post("/register", json={"username": "b", "email": "b@email.com", "password": "b"})
    login = client.post("/login", data={"username": "a", "password": "a"})
    token = login.json()["access_token"]
    client.post("/topics/add", json={"title": "space"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/topics/1/add-member", json={"user_id": "1"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/topics/1/discussion", json={"name": "stars"}, headers={"Authorization": f"Bearer {token}"})

    response_false_no_discussion = client.delete("/topics/delete/1/discussions/100", headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_discussion.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_discussion.json()["detail"] == "Discussion not found"

    response_false_no_topic = client.delete("/topics/delete/10/discussions/1", headers={"Authorization": f"Bearer {token}"})
    assert response_false_no_topic.status_code == HTTP_404_NOT_FOUND
    assert response_false_no_topic.json()["detail"] == "Topic not found"

    login_false = client.post("/login", data={"username": "b", "password": "b"})
    token_false = login_false.json()["access_token"]
    response_false_no_admin = client.delete("/topics/delete/1/discussions/1", headers={"Authorization": f"Bearer {token_false}"})
    assert response_false_no_admin.status_code == HTTP_403_FORBIDDEN
    assert response_false_no_admin.json()["detail"] == "You have to be admin for delete this discussion"

    response_true = client.delete("/topics/delete/1/discussions/1", headers={"Authorization": f"Bearer {token}"})
    assert response_true.status_code == HTTP_200_OK
    assert response_true.json()["message"] == "Discussion has been deleted"