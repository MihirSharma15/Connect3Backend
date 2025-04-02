# tests/test_users.py
from datetime import datetime
import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app
import json
from app.schemas.users import UserInDb
from tests.utils.neo4j_utils import util_create_connection, util_create_user, util_find_user_by_phonenumber

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
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
        "invite_code": "ABCDE"
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

# Also, connection route doesn't seem to update total connections (from lookng at users) - can't check this in create_connection_route_test because when successful, doesn't return anything 
def test_create_connection_route(client, test_neo4j_session):
    """Test for successful connection via standard route."""
    mock_user = {
         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE"
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE"
    }


    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    response = client.post("/users/connect", params={"receiver_number": "+19999999998"})
    print(response.json())
    assert response.status_code == 201


def test_create_connection_route_no_connections(client, test_neo4j_session):
    """Test for unsuccessful connection between users because of no connections remaining."""
    mock_user = {
         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 0,
        "is_verified": True,
        "invite_code": "ABCDE"
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE"
    }

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)

    response = client.post("/users/connect", params={"receiver_number": "+19999999998"})

    assert response.status_code == 405
    assert response.json()["detail"] == "Cannot create connection. User has reached maximum connections."


def test_create_connection_route_already_connected(client, test_neo4j_session):
    """Test for unsuccessful connection between users because they already connected."""
    mock_user = {
         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 1,
        "is_verified": True,
        "invite_code": "ABCDE"
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE"
    }

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    mock_user_obj = UserInDb(**mock_user)
    mock_user_obj2 = UserInDb(**mock_user2)
    util_create_connection(mock_user_obj, mock_user_obj2, test_neo4j_session)

    response = client.post("/users/connect", params={"receiver_number": "+19999999998"})
    assert response.status_code == 400

    data = response.json()
    assert data["detail"] == "Cannot create connection. Users are already directly connected."

# Doesnt work right now - doesn't throw anything when a number doesn't exist in db, because there's no check for receiver user in users.py. Also somehow it connects with proper exit code(?)  
def test_create_connection_route_invalid_phone(client, test_neo4j_session):
    """Test for unsuccessful connection because of an invalid paramaeter."""
    mock_user = {
         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 1,
        "is_verified": True,
        "invite_code": "ABCDE"
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "reated_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE"
    }

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    response = client.post("/users/connect", params={"receiver_number": "+12909934995"})

    assert response.status_code == 500
    assert response.json() == "hello"
    
# DOESN'T WORK - something is wrong with the API logic. It's givng and empty server error too which isn't helpful. Could be the fact that this is a json instead of a query
def test_users_connect_by_code(client, test_neo4j_session):
    """Test for connecting users with connection code."""
    mock_user = {
         "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 1,
        "is_verified": True,
        "invite_code": "ABCDE"
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDF"
    }

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    response = client.post("/users/connect-by-code", json={"code": "ABCDE"})
    assert response.status_code == 202
    assert response.json() == "hello"


def test_graph_user(client, test_neo4j_session):
    """Testing getting the user graph."""
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
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "abcd"
    }
    mock_response = {
        "nodes": [{
            "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
            "name": "John Doe",
            "phonenumber": "+19999999999"
        }],
         "edges": [{
            "source": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
            "target": "db5d23a7-c5b8-4ec1-be46-2028a30261d3"
        }],
    }

    mock_user_obj = UserInDb(**mock_user)
    mock_user_obj2 = UserInDb(**mock_user2)
    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    util_create_connection(mock_user_obj, mock_user_obj2, test_neo4j_session)

    response = client.get("/users/graph", params={"degrees": 1})
    assert response.status_code == 200

    data = response.json()
    assert data["edges"][0]["source"] == mock_response["edges"][0]["source"] 
    assert data["edges"][0]["target"] == mock_response["edges"][0]["target"]
    assert data["nodes"][0]["user_id"] == mock_response["nodes"][0]["user_id"] 
    assert data["nodes"][0]["name"] == mock_response["nodes"][0]["name"]
    assert data["nodes"][0]["phonenumber"] == mock_response["nodes"][0]["phonenumber"]


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
    """Test for searching user and failing because they don't exist in db."""
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
 

def test_user_shortest_path(client, test_neo4j_session):
    """Testing for getting the shortest path for a user"""
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE"
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "Jon Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDF"
    }

    mock_response = {
        "connections": [{
                "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
                "name": "John Doe",
                "phonenumber": "+19999999999"
            }]
    }
    mock_phone_number = "+19999999998"


    mock_user_obj = UserInDb(**mock_user)
    mock_user2_obj = UserInDb(**mock_user2)


    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    util_create_connection(mock_user_obj, mock_user2_obj, test_neo4j_session)

    response = client.get(f"/users/{mock_phone_number}/shortest-path")
    assert response.status_code == 200
    data = response.json()

    assert data["connections"][0]["user_id"] == mock_response["connections"][0]["user_id"]
    assert data["connections"][0]["name"] == mock_response["connections"][0]["name"]
    assert data["connections"][0]["phonenumber"] == mock_response["connections"][0]["phonenumber"]


def test_user_shortest_path_no_connections(client, test_neo4j_session):
    """Testing for getting the shortest path for users that aren't connected."""
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE"
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "Jon Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDF"
    }

    mock_phone_number = "+19999999998"

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)

    response = client.get(f"/users/{mock_phone_number}/shortest-path")
    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "Path Not Found"

   


    




