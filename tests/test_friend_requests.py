import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_406_NOT_ACCEPTABLE
from main import app
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

#=========================TESTS============================#
#Register helper
def register(username, email):
    return client.post("/register", json={"username": username , "email": email, "password":"password123"} )

#login Helper
def login(username):
    response = client.post("/login", data={"username": username, "password":"password123"})
    return response.json()["access_token"]

def test_send_friend_request_success():
    register("sender_user", "sender@test.com")
    token_sender = login("sender_user")

    res_receiver = register("receiver_user", "receiver@test")
    receiver_id = res_receiver.json()["id"]

    response = client.post(f"/friend/request/{receiver_id}",
                           headers = {"Authorization": f"Bearer {token_sender}"})

    assert response.status_code == HTTP_201_CREATED
    assert response.json()["receiver_id"] == receiver_id
    assert response.json()["status"] == "pending"

def test_send_request_yourself_fail():
    res_user = register("yourself", "yourself@test")
    token_sender = login("yourself")
    user_id = res_user.json()["id"]

    response = client.post(f"/friend/request/{user_id}",
                           headers = {"Authorization": f"Bearer {token_sender}"})

    assert response.status_code == HTTP_406_NOT_ACCEPTABLE
    assert response.json()["detail"] == "You can not send a friend request to yourself."

def test_list_pending_requests():
    user_a = register(username="userA", email="A@test")
    token_a = login("userA")
    a_id = user_a.json()["id"]

    user_b = register(username="userB", email="B@test")
    token_b = login("userB")
    b_id = user_b.json()["id"]

    client.post(f"/friend/request/{b_id}",
                headers = {"Authorization": f"Bearer {token_a}"})

    response = client.get("/friend/requests/pending",
                          headers = {"Authorization": f"Bearer {token_b}"})

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["sender_id"] == a_id

def test_list_requests_empty():
    register("empty", "empty@test")
    token_empty = login("empty")

    response = client.get("/friend/requests/pending",
                          headers = {"Authorization": f"Bearer {token_empty}"})

    assert response.status_code == HTTP_200_OK
    assert response.json() == []

def test_accept_friend_request_success():
    register("sender_A", "senderA@test")
    token_sender_a = login("sender_A")

    res_b = register(username="receiverB", email="receiverB@test")
    receiver_b_id = res_b.json()["id"]
    token_receiver_b = login("receiverB")

    send_request = client.post(f"/friend/request/{receiver_b_id}",
                                   headers= {"Authorization": f"Bearer {token_sender_a}"})
    request_id = send_request.json()["id"]

    accept_request = client.put(f"/friends/request/{request_id}/accept",
                                headers={"Authorization": f"Bearer {token_receiver_b}"})

    assert accept_request.status_code == HTTP_200_OK
    assert accept_request.json()["status"] == "accepted"

def test_reject_friend_request_success():
    register("rejectA", "rejectA@test")
    token_reject_a = login("rejectA")

    res_reject_b = register(username="rejectB", email="rejectB@test")
    receiver_b_id = res_reject_b.json()["id"]
    token_reject_b = login("rejectB")

    send_request = client.post(f"/friend/request/{receiver_b_id}",
                               headers = {"Authorization": f"Bearer {token_reject_a}"})
    request_id = send_request.json()["id"]

    reject_request = client.put(f"/friends/request/{request_id}/reject",
                                headers={"Authorization": f"Bearer {token_reject_b}"})

    assert reject_request.status_code == HTTP_200_OK
    assert reject_request.json()["status"] == "rejected"

def test_respond_others_requests():
    register("user1", "user1@test")
    token_user1 = login("user1")

    receiver_user2 = register(username="user2", email="user2@test")
    receiver_user2_id = receiver_user2.json()["id"]

    register("other_user3", "otheruser3@test")
    token_other_user3 = login("other_user3")

    request_send = client.post(f"/friend/request/{receiver_user2_id}",
                               headers={"Authorization": f"Bearer {token_user1}"})
    request_id = request_send.json()["id"]

    other_tries_accept = client.put(f"friend/request/{request_id}/accept",
                                    headers={"Authorization": f"Bearer {token_other_user3}"})

    assert other_tries_accept.status_code == HTTP_404_NOT_FOUND
    assert other_tries_accept.json()["detail"] == "Not Found"