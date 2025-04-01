# tests/test_users.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.utils.neo4j_utils import util_create_user

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


    response = client.post("/users/", json=test_user)
    assert response.status_code == 201

    data = response.json()
    assert data["phonenumber"] == test_user["phonenumber"]
    assert data["name"] == test_user["name"]
    assert "created_at" in data
    assert "remaining_connections" in data
    assert "is_verified" in data

# Second test for if create user fails here

def test_get_users(client):
    """Test getting user data."""
     
    mock_user = {
        "user_id": "abc",
        "name": "John Doe",
        "phonenumber": "+11234567890",
        "created_at": "time",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "abc"
     }
    
    response = client.post("/users/me", json=mock_user)
    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == mock_user["user_id"]
    assert data["name"] == mock_user["name"]
    assert data["phonenumber"] == mock_user["phonenumber"]
    assert data["created_at"] == mock_user["created_at"]
    assert data["is_verified"] == mock_user["is_verified"]
    assert data["invite_code"] == mock_user["invite_code"]

# No case for test fail user(?)

# def test_successful_connect_user(client):
#     """Test for successful."""


def test_search_user(client):
    mock_user = {
        "user_id": "abc",
        "name": "John Doe",
        "phonenumber": "+11234567890",
        "created_at": "time",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "abc"
     }
    
    mock_phone_number = "+11234567890"
    response = client.post("/users/{mock_phone_number}", json=mock_user)
    assert response.status_code == 201

    data = response.json()
    assert data["user_id"] == mock_user["user_id"]
    assert data["name"] == mock_user["name"]
    assert data["phonenumber"] == mock_user["phonenumber"]
    assert data["created_at"] == mock_user["created_at"]
    assert data["is_verified"] == mock_user["is_verified"]
    assert data["invite_code"] == mock_user["invite_code"]    

def test_user_shortest_path(client):
    mock_user = {
        "user_id": "abc",
        "name": "John Doe",
        "phonenumber": "+11234567890",
        "created_at": "time",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "abc"
     }
    
    mock_phone_number = "+11234567890"
    response = client.post("/users/{mock_phone_number}/shortest_path", json=mock_user)
    assert response.status_code == 201
   
    data = response.json()
    assert data["user_id"] == mock_user["user_id"]
    assert data["name"] == mock_user["name"]
    assert data["phonenumber"] == mock_user["phonenumber"]
    




