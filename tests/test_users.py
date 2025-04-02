# tests/test_users.py
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
import json
from app.schemas.users import UserInDb
from tests.utils.neo4j_utils import util_create_connection, util_create_user

client = TestClient(app)

"""'
TESTS ALL ROUTES FOR THE /USERS ENDPOINT

The following test cases need to be done.

1] /users -> creating a user 
2] /users/me -> gets the current user 
3] /connect -> connects a user to another user 
4] /graph -> returns the graphical representation of the user and their connections 
5] /{phonenumber} -> returns a user given that phone number
6] /{phonenumber}/connections -> returns the shortest path between two users given their phone numbers

NOTE: there should >6 test cases in this file, one for each of the above endpoints and one for each of the possible outcomes (success and failure) for each endpoint. for example, test cases for when the user is not found, then a user doesn't have any more connections, etc. 

"""

# example: (notice how client is in the header i spent 2 hours figuring this out)
def test_create_user(client, test_neo4j_session):
    """Tests the /users endpoint for creating a user."""

    test_user = {
        "phonenumber": "+11234567890",
        "name": "John Doe",
        "hashed_password": "fakehashedpassword"
    }

    fake_user = {
        "phonenumber": "+11234599999",
        "name": "John Jeer",
        "hashed_password": "fakehashedpassword"
    }

    util_create_user(fake_user, session=test_neo4j_session)

    response = client.post("/users/", json=test_user)
    assert response.status_code == 201

    data = response.json()
    assert data["phonenumber"] == test_user["phonenumber"]
    assert data["name"] == test_user["name"]
    assert "created_at" in data
    assert "remaining_connections" in data
    assert "is_verified" in data

def test_successful_get_users(client, test_neo4j_session):
    """Test getting user data."""
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "abc"
     }
    
    util_create_user(mock_user, test_neo4j_session)
    response = client.get("/users/me")
    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == mock_user["user_id"]
    assert data["name"] == mock_user["name"]
    assert data["phonenumber"] == mock_user["phonenumber"]
    assert data["created_at"] == mock_user["created_at"]
    assert data["is_verified"] == mock_user["is_verified"]
    assert data["invite_code"] == mock_user["invite_code"]



# def test_create_connection_route(client, test_neo4j_session):
#     """Test for successful connection via standard route."""
#     mock_user = {
#          "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
#         "name": "John Doe",
#         "phonenumber": "+19999999999",
#         "hashed_password": "fakehashedpassword",
#         "created_at": "1-1-1970",
#         "remaining_connections": 2,
#         "is_verified": True,
#         "invite_code": "abc"
#     }
#     mock_user2 = {
#         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
#         "name": "John Doe",
#         "phonenumber": "+19999999998",
#         "hashed_password": "fakehashedpassword",
#         "created_at": "1-1-1970",
#         "remaining_connections": 2,
#         "is_verified": True,
#         "invite_code": "abc"
#     }


#     util_create_user(mock_user, test_neo4j_session)
#     util_create_user(mock_user2, test_neo4j_session)
#     mock_user_obj = UserInDb(**mock_user)
#     mock_user_obj2 = UserInDb(**mock_user2)
#     response = client.post("/users/connect", json={'reciever_number':"+19999999998"})
#     assert response.status_code == 201


# def test_graph_user(client, test_neo4j_session):
#     mock_user = {
#         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
#         "name": "John Doe",
#         "phonenumber": "+19999999999",
#         "hashed_password": "fakehashedpassword",
#         "created_at": "1-1-1970",
#         "remaining_connections": 3,
#         "is_verified": True,
#         "invite_code": "abc"
#     }
#     mock_user2 = {
#         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
#         "name": "John Doe",
#         "phonenumber": "+19999999998",
#         "hashed_password": "fakehashedpassword",
#         "created_at": "1-1-1970",
#         "remaining_connections": 3,
#         "is_verified": True,
#         "invite_code": "abcd"
#     }
#     mock_user_obj = UserInDb(**mock_user)
#     mock_user_obj2 = UserInDb(**mock_user2)
#     util_create_user(mock_user, test_neo4j_session)
#     # util_create_user(mock_user2, test_neo4j_session)
#     # util_create_connection(mock_user_obj, mock_user_obj2, test_neo4j_session)

#     response = client.get("/users/graph", params="19999999999")
#     assert response.status_code == 200
#     print(response.json)

    


def test_search_user(client, test_neo4j_session):
    """Test for searching user."""
    mock_user = {
         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "abc"
     }
    
    util_create_user(mock_user, test_neo4j_session)
    response = client.get("/users/+19999999999")
    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == mock_user["user_id"]
    assert data["name"] == mock_user["name"]
    assert data["phonenumber"] == mock_user["phonenumber"]
    assert data["created_at"] == mock_user["created_at"]
    assert data["is_verified"] == mock_user["is_verified"]
    assert data["invite_code"] == mock_user["invite_code"]

def test_unsuccesful_search_user(client, test_neo4j_session):
    """Test for searching user and failing."""
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 1,
        "is_verified": True,
        "invite_code": "abc"
     }
    
    util_create_user(mock_user, test_neo4j_session)
    response = client.get("/users/+19999999998")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found in DB"
 

# def test_user_shortest_path(client):
#     mock_user = {
#         "user_id": "abc",
#         "name": "John Doe",
#         "phonenumber": "+11234567890",
#         "created_at": "time",
#         "remaining_connections": 2,
#         "is_verified": True,
#         "invite_code": "abc"
#      }
    
#     mock_phone_number = "+11234567890"
#     response = client.post("/users/{mock_phone_number}/shortest_path", json=mock_user)
#     assert response.status_code == 201
   
#     data = response.json()
#     assert data["user_id"] == mock_user["user_id"]
#     assert data["name"] == mock_user["name"]
#     assert data["phonenumber"] == mock_user["phonenumber"]
    




