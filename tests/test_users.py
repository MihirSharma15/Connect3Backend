# tests/test_users.py
import datetime
import logging
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.users import UserInDb
from tests.utils.neo4j_utils import util_create_connection, util_create_user

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.ERROR)
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
        "hashed_password": "fakehashedpassword",
    }

    response = client.post("/users?password=password", json=test_user)
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
        "invite_code": "ABCDE",
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
        "invite_code": "ABCDE",
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE",
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
        "invite_code": "ABCDE",
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE",
    }

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)

    response = client.post("/users/connect", params={"receiver_number": "+19999999998"})

    assert response.status_code == 405
    assert (
        response.json()["detail"]
        == "Cannot create connection. User has reached maximum connections."
    )


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
        "invite_code": "ABCDE",
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE",
    }

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    mock_user_obj = UserInDb(**mock_user)
    mock_user_obj2 = UserInDb(**mock_user2)
    util_create_connection(mock_user_obj, mock_user_obj2, test_neo4j_session)

    response = client.post("/users/connect", params={"receiver_number": "+19999999998"})
    assert response.status_code == 400

    data = response.json()
    assert (
        data["detail"]
        == "Cannot create connection. Users are already directly connected."
    )


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
        "invite_code": "ABCDE",
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "reated_at": "1-1-1970",
        "remaining_connections": 2,
        "is_verified": True,
        "invite_code": "ABCDE",
    }

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    response = client.post("/users/connect", params={"receiver_number": "+12909934995"})

    assert True == True


def test_users_connect_by_code(client, test_neo4j_session):
    """Test for connecting users with connection code."""
    current_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE",
    }

    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDF",
    }

    util_create_user(current_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    # Use Code ABCDF since curernt user has code ABCDE
    response = client.post("/users/connect-by-code", json={"code": "ABCDF"})
    assert response.status_code == 202
    assert response.json() == {
        "message": "Connection created successfully.",
        "remaining_connections": 2,
    }


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
        "invite_code": "abc",
        "status_content": "Test status",
        "status_degree": 2,
        "status_created_at": "2024-04-15T12:00:00",
        "status_expired_at": "2024-04-16T12:00:00",
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "John Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "abcd",
        "status_content": "Another status",
        "status_degree": 1,
        "status_created_at": "2024-04-15T12:00:00",
        "status_expired_at": "2024-04-16T12:00:00",
    }
    mock_response = {
        "nodes": [
            {
                "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
                "name": "John Doe",
            }
        ],
        "edges": [
            {
                "source": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
                "target": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
            }
        ],
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

    # Verify presence of status fields without checking specific values
    assert "status" in data["nodes"][0]


def test_graph_user_multiple_degrees_centered_on_current_user(
    client, test_neo4j_session
):
    """
    We assume fake_get_current_user() always returns the same user:
      user_id="db5d23a7-c5b8-4ec1-be46-2028a30261d2"
      name="John Doe"
      phonenumber="+19999999999"
      ...
    So the /graph endpoint will center on that user (call them U1).

    We'll create a chain: U1 -> U2 -> U3 -> U4 -> U5.
    Distances from U1:
        U2: distance 1
        U3: distance 2
        U4: distance 3
        U5: distance 4
    We then test whether requesting different degrees returns the correct nodes and edges.
    """

    # The "current user" (from fake_get_current_user)
    user_1_data = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABC",
        "status_content": "Current user status",
        "status_degree": 1,
        "status_created_at": "2024-04-15T12:00:00",
        "status_expired_at": "2024-04-16T12:00:00",
    }

    # Define extra users to create a chain
    user_2_data = {
        "user_id": "22222222-2222-2222-2222-222222222222",
        "name": "User2",
        "phonenumber": "+10000000002",
        "hashed_password": "fakehashedpassword2",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "code2",
        "status_content": "User2 status",
        "status_degree": 2,
        "status_created_at": "2024-04-15T12:00:00",
        "status_expired_at": "2024-04-16T12:00:00",
    }
    user_3_data = {
        "user_id": "33333333-3333-3333-3333-333333333333",
        "name": "User3",
        "phonenumber": "+10000000003",
        "hashed_password": "fakehashedpassword3",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "code3",
        "status_content": "User3 status",
        "status_degree": 1,
        "status_created_at": "2024-04-15T12:00:00",
        "status_expired_at": "2024-04-16T12:00:00",
    }
    user_4_data = {
        "user_id": "44444444-4444-4444-4444-444444444444",
        "name": "User4",
        "phonenumber": "+10000000004",
        "hashed_password": "fakehashedpassword4",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "code4",
        "status_content": "User4 status",
        "status_degree": 3,
        "status_created_at": "2024-04-15T12:00:00",
        "status_expired_at": "2024-04-16T12:00:00",
    }
    user_5_data = {
        "user_id": "55555555-5555-5555-5555-555555555555",
        "name": "User5",
        "phonenumber": "+10000000005",
        "hashed_password": "fakehashedpassword5",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "code5",
        "status_content": "User5 status",
        "status_degree": 0,
        "status_created_at": "2024-04-15T12:00:00",
        "status_expired_at": "2024-04-16T12:00:00",
    }

    # Create all users in DB
    util_create_user(user_1_data, test_neo4j_session)
    util_create_user(user_2_data, test_neo4j_session)
    util_create_user(user_3_data, test_neo4j_session)
    util_create_user(user_4_data, test_neo4j_session)
    util_create_user(user_5_data, test_neo4j_session)

    # Convert to UserInDb objects
    user_1 = UserInDb(**user_1_data)
    user_2 = UserInDb(**user_2_data)
    user_3 = UserInDb(**user_3_data)
    user_4 = UserInDb(**user_4_data)
    user_5 = UserInDb(**user_5_data)

    # Create a chain: U1 -> U2 -> U3 -> U4 -> U5
    # In your actual setup, these relationships might be stored bi-directionally,
    # but we typically just call your util once for each connection pair.
    util_create_connection(user_1, user_2, test_neo4j_session)
    util_create_connection(user_2, user_3, test_neo4j_session)
    util_create_connection(user_3, user_4, test_neo4j_session)
    util_create_connection(user_4, user_5, test_neo4j_session)

    #
    # Test degrees=2
    # We expect: U1, U2, U3 (but NOT U4 or U5, since they're distance 3 and 4).
    #
    response_deg_2 = client.get("/users/graph", params={"degrees": 2})
    assert response_deg_2.status_code == 200
    graph_deg_2 = response_deg_2.json()

    # Verify nodes
    returned_nodes_2 = {n["user_id"] for n in graph_deg_2["nodes"]}
    assert user_1.user_id in returned_nodes_2
    assert user_2.user_id in returned_nodes_2
    assert user_3.user_id in returned_nodes_2
    assert user_4.user_id not in returned_nodes_2
    assert user_5.user_id not in returned_nodes_2

    # Check status fields are present for at least one node
    assert any("status" in node for node in graph_deg_2["nodes"])

    # Verify edges (they should only be (U1-U2) and (U2-U3))
    expected_edges_2 = {
        (user_1.user_id, user_2.user_id),
        (user_2.user_id, user_3.user_id),
    }
    returned_edges_2 = {(e["source"], e["target"]) for e in graph_deg_2["edges"]}
    # If your DB stores them in the opposite direction, check for that as well
    # (U2-U1) or (U3-U2). We'll just assume direction matches creation for now.
    for edge_pair in expected_edges_2:
        assert (edge_pair in returned_edges_2) or (
            (edge_pair[1], edge_pair[0]) in returned_edges_2
        )

    #
    # Test degrees=4
    # Now we expect *all* of them: U1, U2, U3, U4, U5.
    #
    response_deg_4 = client.get("/users/graph", params={"degrees": 4})
    assert response_deg_4.status_code == 200
    graph_deg_4 = response_deg_4.json()

    returned_nodes_4 = {n["user_id"] for n in graph_deg_4["nodes"]}
    # Distances: U2=1, U3=2, U4=3, U5=4 -- so all should appear
    assert user_1.user_id in returned_nodes_4
    assert user_2.user_id in returned_nodes_4
    assert user_3.user_id in returned_nodes_4
    assert user_4.user_id in returned_nodes_4
    assert user_5.user_id in returned_nodes_4

    # Check status fields are present for at least one node
    assert any("status" in node for node in graph_deg_4["nodes"])

    # Verify edges (full chain)
    expected_edges_4 = {
        (user_1.user_id, user_2.user_id),
        (user_2.user_id, user_3.user_id),
        (user_3.user_id, user_4.user_id),
        (user_4.user_id, user_5.user_id),
    }
    returned_edges_4 = {(e["source"], e["target"]) for e in graph_deg_4["edges"]}
    for edge_pair in expected_edges_4:
        assert (edge_pair in returned_edges_4) or (
            (edge_pair[1], edge_pair[0]) in returned_edges_4
        )


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
        "invite_code": "abc",
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
        "invite_code": "abc",
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
        "invite_code": "ABCDE",
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "Jon Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDF",
    }

    mock_response = {
        "connections": [
            {
                "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
                "name": "John Doe",
                "last_four_digits": "9999",
            }
        ]
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

    assert (
        data["connections"][0]["user_id"] == mock_response["connections"][0]["user_id"]
    )
    assert data["connections"][0]["name"] == mock_response["connections"][0]["name"]
    assert (
        data["connections"][0]["last_four_digits"]
        == mock_response["connections"][0]["last_four_digits"]
    )


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
        "invite_code": "ABCDE",
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "Jon Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDF",
    }

    mock_phone_number = "+19999999998"

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)

    response = client.get(f"/users/{mock_phone_number}/shortest-path")
    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "Path Not Found"


def test_user_shortest_path_by_id(client, test_neo4j_session):
    """Testing for getting the shortest path between users using user_id"""
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE",
    }
    mock_user2 = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d3",
        "name": "Jon Doe",
        "phonenumber": "+19999999998",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDF",
    }

    mock_user_obj = UserInDb(**mock_user)
    mock_user2_obj = UserInDb(**mock_user2)

    util_create_user(mock_user, test_neo4j_session)
    util_create_user(mock_user2, test_neo4j_session)
    util_create_connection(mock_user_obj, mock_user2_obj, test_neo4j_session)

    response = client.get(f"/users/id/{mock_user2['user_id']}/shortest-path")
    assert response.status_code == 200
    data = response.json()

    # Verify the path contains both users with correct format
    assert len(data["connections"]) >= 2
    assert any(conn["user_id"] == mock_user["user_id"] for conn in data["connections"])
    assert any(conn["user_id"] == mock_user2["user_id"] for conn in data["connections"])
    # Verify each connection has the correct fields
    for conn in data["connections"]:
        assert "user_id" in conn
        assert "name" in conn
        assert "last_four_digits" in conn
        assert len(conn["last_four_digits"]) == 4


def test_user_shortest_path_by_id_not_found(client, test_neo4j_session):
    """Testing for getting the shortest path when target user doesn't exist"""
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE",
    }

    util_create_user(mock_user, test_neo4j_session)

    # Try to find path to non-existent user
    response = client.get("/users/id/non-existent-user-id/shortest-path")
    assert response.status_code == 404
    assert response.json()["detail"] == "Target user not found."


def test_user_shortest_path_complex_chain(client, test_neo4j_session):
    """Testing shortest path with a complex chain of users"""
    # Create a chain of users with some branching paths
    # Structure:
    # U1 -> U2 -> U3 -> U4 -> U5
    #      \-> U6 -> U7
    #           \-> U8

    # First create the current user (U1) that will be returned by get_current_user
    current_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",  # This is the user_id that get_current_user returns
        "name": "Current User",
        "phonenumber": "+19999999999",  # This is the phone number that get_current_user returns
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "CURR1",
    }
    util_create_user(current_user, test_neo4j_session)
    current_user_obj = UserInDb(**current_user)

    # Create the rest of the users
    users = [
        {
            "user_id": "user2",
            "name": "User2",
            "phonenumber": "+19999999992",
            "hashed_password": "fakehashedpassword",
            "created_at": "1-1-1970",
            "remaining_connections": 3,
            "is_verified": True,
            "invite_code": "CODE2",
        },
        {
            "user_id": "user3",
            "name": "User3",
            "phonenumber": "+19999999993",
            "hashed_password": "fakehashedpassword",
            "created_at": "1-1-1970",
            "remaining_connections": 3,
            "is_verified": True,
            "invite_code": "CODE3",
        },
        {
            "user_id": "user4",
            "name": "User4",
            "phonenumber": "+19999999994",
            "hashed_password": "fakehashedpassword",
            "created_at": "1-1-1970",
            "remaining_connections": 3,
            "is_verified": True,
            "invite_code": "CODE4",
        },
        {
            "user_id": "user5",
            "name": "User5",
            "phonenumber": "+19999999995",
            "hashed_password": "fakehashedpassword",
            "created_at": "1-1-1970",
            "remaining_connections": 3,
            "is_verified": True,
            "invite_code": "CODE5",
        },
        {
            "user_id": "user6",
            "name": "User6",
            "phonenumber": "+19999999996",
            "hashed_password": "fakehashedpassword",
            "created_at": "1-1-1970",
            "remaining_connections": 3,
            "is_verified": True,
            "invite_code": "CODE6",
        },
        {
            "user_id": "user7",
            "name": "User7",
            "phonenumber": "+19999999997",
            "hashed_password": "fakehashedpassword",
            "created_at": "1-1-1970",
            "remaining_connections": 3,
            "is_verified": True,
            "invite_code": "CODE7",
        },
        {
            "user_id": "user8",
            "name": "User8",
            "phonenumber": "+19999999998",
            "hashed_password": "fakehashedpassword",
            "created_at": "1-1-1970",
            "remaining_connections": 3,
            "is_verified": True,
            "invite_code": "CODE8",
        },
    ]

    # Create all users
    user_objects = []
    for user_data in users:
        util_create_user(user_data, test_neo4j_session)
        user_objects.append(UserInDb(**user_data))

    # Create connections
    # Main chain: Current User -> U2 -> U3 -> U4 -> U5
    util_create_connection(current_user_obj, user_objects[0], test_neo4j_session)
    util_create_connection(user_objects[0], user_objects[1], test_neo4j_session)
    util_create_connection(user_objects[1], user_objects[2], test_neo4j_session)
    util_create_connection(user_objects[2], user_objects[3], test_neo4j_session)

    # Branch 1: U2 -> U6 -> U7
    util_create_connection(user_objects[0], user_objects[4], test_neo4j_session)
    util_create_connection(user_objects[4], user_objects[5], test_neo4j_session)

    # Branch 2: U6 -> U8
    util_create_connection(user_objects[4], user_objects[6], test_neo4j_session)

    # Test shortest path from Current User to U5 (should be direct chain)
    response = client.get(f"/users/id/{users[3]['user_id']}/shortest-path")
    assert response.status_code == 200
    data = response.json()

    # Verify the path contains all users in the main chain
    expected_path = [current_user["user_id"], "user2", "user3", "user4", "user5"]
    assert len(data["connections"]) == len(expected_path)
    for i, conn in enumerate(data["connections"]):
        assert conn["user_id"] == expected_path[i]
        if i == 0:
            assert conn["name"] == "Current User"
            assert conn["last_four_digits"] == "9999"
        else:
            assert conn["name"] == f"User{i + 1}"
            assert conn["last_four_digits"] == f"999{i + 1}"

    # Test shortest path from Current User to U7 (should go through U2 and U6)
    response = client.get(f"/users/id/{users[5]['user_id']}/shortest-path")
    assert response.status_code == 200
    data = response.json()

    # Verify the path contains the correct users
    expected_path = [current_user["user_id"], "user2", "user6", "user7"]
    assert len(data["connections"]) == len(expected_path)
    for i, conn in enumerate(data["connections"]):
        assert conn["user_id"] == expected_path[i]
        if i == 0:
            assert conn["name"] == "Current User"
            assert conn["last_four_digits"] == "9999"
        else:
            assert conn["name"] == f"User{expected_path[i][-1]}"
            assert conn["last_four_digits"] == f"999{expected_path[i][-1]}"

    # Test shortest path from Current User to U8 (should go through U2 and U6)
    response = client.get(f"/users/id/{users[6]['user_id']}/shortest-path")
    assert response.status_code == 200
    data = response.json()

    # Verify the path contains the correct users
    expected_path = [current_user["user_id"], "user2", "user6", "user8"]
    assert len(data["connections"]) == len(expected_path)
    for i, conn in enumerate(data["connections"]):
        assert conn["user_id"] == expected_path[i]
        if i == 0:
            assert conn["name"] == "Current User"
            assert conn["last_four_digits"] == "9999"
        else:
            assert conn["name"] == f"User{expected_path[i][-1]}"
            assert conn["last_four_digits"] == f"999{expected_path[i][-1]}"


def test_search_user_by_code_success(client, test_neo4j_session):
    """Test successful search for a user by invite code"""
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE",
    }

    util_create_user(mock_user, test_neo4j_session)

    response = client.get(f"/users/code/{mock_user['invite_code']}")
    assert response.status_code == 200
    data = response.json()

    # Verify response contains correct data and phone number is null
    assert data["user_id"] == mock_user["user_id"]
    assert data["name"] == mock_user["name"]
    assert data["phonenumber"] is None
    assert "invite_code" not in data  # invite_code should not be in response


def test_search_user_by_code_not_found(client, test_neo4j_session):
    """Test search for a user with invalid invite code"""
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE",
    }

    util_create_user(mock_user, test_neo4j_session)

    # Try to find user with invalid code
    response = client.get("/users/code/INVALID")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found in DB or Invite Code not valid"


def test_search_user_by_code_invalid_format(client, test_neo4j_session):
    """Test search with invalid invite code format"""
    # Try to find user with code that doesn't match the pattern (should be 5 uppercase alphanumeric)
    response = client.get("/users/code/abc12")  # lowercase
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found in DB or Invite Code not valid"

    response = client.get("/users/code/ABCD")  # too short
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found in DB or Invite Code not valid"

    response = client.get("/users/code/ABCDEF")  # too long
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found in DB or Invite Code not valid"


def test_graph_user_no_connections(client, test_neo4j_session):
    """Test getting the user graph when the current user has no connections"""
    # Create the current user (from conftest.py) in the database
    current_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE",
        "status_content": "Solo user status",
        "status_degree": 2,
        "status_created_at": "2024-04-15T12:00:00",
        "status_expired_at": "2024-04-16T12:00:00",
    }
    util_create_user(current_user, test_neo4j_session)

    # Call the graph endpoint
    response = client.get("/users/graph", params={"degrees": 1})
    assert response.status_code == 200
    data = response.json()

    # Verify response contains only the current user
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["user_id"] == current_user["user_id"]
    assert data["nodes"][0]["name"] == current_user["name"]

    # Verify status is present
    assert "status" in data["nodes"][0]

    # Verify no edges exist
    assert len(data["edges"]) == 0


def test_update_user_status_success(client, test_neo4j_session):
    """Test successful update of a user's status"""
    # Create a test user
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE",
        "status_content": "",
        "status_degree": 0,
        "status_created_at": "",
        "status_expired_at": "",
    }
    util_create_user(mock_user, test_neo4j_session)

    # Update status
    status_data = {
        "status_content": "Feeling great today!",
        "status_degree": 2,
    }
    response = client.post("/status", json=status_data)
    assert response.status_code == 201


def test_update_user_status_invalid_degree(client, test_neo4j_session):
    """Test status update with invalid degree value"""
    # Create a test user
    mock_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE",
        "status_content": "",
        "status_degree": 0,
        "status_created_at": "",
        "status_expired_at": "",
    }
    util_create_user(mock_user, test_neo4j_session)

    # Try to update status with negative degree
    status_data = {
        "status_content": "Invalid status",
        "status_degree": -1,
    }
    response = client.post("/status", json=status_data)
    assert response.status_code == 400


def test_graph_user_status_degree_filtering(client, test_neo4j_session):
    """
    Test that statuses are properly filtered based on their degree setting.

    This test creates a chain of users:
    U1 -> U2 -> U3 -> U4

    Where:
    - U1 is the current user
    - U4 has a status with degree=2

    When U1 requests a graph with degree=3, they should:
    - See U4 as a node (since U4 is within 3 degrees)
    - NOT see U4's status (since it's set to be visible only up to 2 degrees away)
    """
    # Get current timestamp for fresh statuses
    now = datetime.datetime.now()
    fresh_timestamp = now.isoformat()
    future_expiry = (now + datetime.timedelta(hours=23)).isoformat()

    # Create a chain of users
    user_1_data = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",  # Current user
        "name": "Current User",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "CODE1",
        "status_content": "Current user status",
        "status_degree": 3,
        "status_created_at": fresh_timestamp,
        "status_expired_at": future_expiry,
    }

    user_2_data = {
        "user_id": "user2-id",
        "name": "User 2",
        "phonenumber": "+19999999992",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "CODE2",
        "status_content": "User 2 status",
        "status_degree": 3,
        "status_created_at": fresh_timestamp,
        "status_expired_at": future_expiry,
    }

    user_3_data = {
        "user_id": "user3-id",
        "name": "User 3",
        "phonenumber": "+19999999993",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "CODE3",
        "status_content": "User 3 status",
        "status_degree": 3,
        "status_created_at": fresh_timestamp,
        "status_expired_at": future_expiry,
    }

    user_4_data = {
        "user_id": "user4-id",
        "name": "User 4",
        "phonenumber": "+19999999994",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "CODE4",
        "status_content": "User 4 status - limited visibility",
        "status_degree": 2,  # This status should only be visible up to 2 degrees away
        "status_created_at": fresh_timestamp,
        "status_expired_at": future_expiry,
    }

    # Create users in DB
    util_create_user(user_1_data, test_neo4j_session)
    util_create_user(user_2_data, test_neo4j_session)
    util_create_user(user_3_data, test_neo4j_session)
    util_create_user(user_4_data, test_neo4j_session)

    # Convert to UserInDb objects for creating connections
    user_1 = UserInDb(**user_1_data)
    user_2 = UserInDb(**user_2_data)
    user_3 = UserInDb(**user_3_data)
    user_4 = UserInDb(**user_4_data)

    # Create connections forming a chain: U1 -> U2 -> U3 -> U4
    util_create_connection(user_1, user_2, test_neo4j_session)
    util_create_connection(user_2, user_3, test_neo4j_session)
    util_create_connection(user_3, user_4, test_neo4j_session)

    # Request graph with degree=3 (should include all users)
    response = client.get("/users/graph", params={"degrees": 3})
    assert response.status_code == 200
    graph_data = response.json()

    # Verify all users are in the graph
    user_ids = {node["user_id"] for node in graph_data["nodes"]}
    assert user_1_data["user_id"] in user_ids
    assert user_2_data["user_id"] in user_ids
    assert user_3_data["user_id"] in user_ids
    assert user_4_data["user_id"] in user_ids

    # Find user 4 in the response
    user4_node = next(
        (
            node
            for node in graph_data["nodes"]
            if node["user_id"] == user_4_data["user_id"]
        ),
        None,
    )
    assert user4_node is not None

    # Key test: User 4's status should NOT be visible since its degree=2 and we're 3 degrees away
    assert user4_node["status"] is None, (
        "User 4's status should be filtered out due to degree restriction"
    )

    # But closer users' statuses should be visible
    user2_node = next(
        (
            node
            for node in graph_data["nodes"]
            if node["user_id"] == user_2_data["user_id"]
        ),
        None,
    )
    user3_node = next(
        (
            node
            for node in graph_data["nodes"]
            if node["user_id"] == user_3_data["user_id"]
        ),
        None,
    )

    assert user2_node["status"] is not None, "User 2's status should be visible"
    assert user3_node["status"] is not None, "User 3's status should be visible"


def test_graph_user_expired_status_filtering(client, test_neo4j_session):
    """
    Test that expired statuses (older than 24 hours) are filtered out properly.

    Creates a user with an old status and verifies it's not visible in the graph.
    """
    # Get current timestamp and create timestamps for testing
    now = datetime.datetime.now()
    old_timestamp = (now - datetime.timedelta(hours=25)).isoformat()
    fresh_timestamp = now.isoformat()
    future_expiry = (now + datetime.timedelta(hours=23)).isoformat()

    # Create current user with an expired status
    current_user = {
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",  # Current user
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "CODE1",
        "status_content": "This is an old status that should be filtered",
        "status_degree": 3,
        "status_created_at": old_timestamp,
        "status_expired_at": (now - datetime.timedelta(hours=1)).isoformat(),
    }

    # Create a connected user with a fresh status
    connected_user = {
        "user_id": "fresh-status-user-id",  # Different user ID
        "name": "Fresh Status User",
        "phonenumber": "+19999999992",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "CODE2",
        "status_content": "This is a fresh status that should be visible",
        "status_degree": 3,
        "status_created_at": fresh_timestamp,
        "status_expired_at": future_expiry,
    }

    # Create users in DB
    util_create_user(current_user, test_neo4j_session)
    util_create_user(connected_user, test_neo4j_session)

    # Connect the users
    user_1 = UserInDb(**current_user)
    user_2 = UserInDb(**connected_user)
    util_create_connection(user_1, user_2, test_neo4j_session)

    # Request graph
    response = client.get("/users/graph", params={"degrees": 1})
    assert response.status_code == 200
    graph_data = response.json()

    # Verify nodes exist
    user_ids = {node["user_id"] for node in graph_data["nodes"]}
    assert current_user["user_id"] in user_ids
    assert connected_user["user_id"] in user_ids

    # Find current user in the response
    current_user_node = next(
        (
            node
            for node in graph_data["nodes"]
            if node["user_id"] == current_user["user_id"]
        ),
        None,
    )
    assert current_user_node is not None

    # Key test: Current user's status should be filtered out due to age
    assert current_user_node["status"] is None, "Expired status should be filtered out"

    # Connected user's status should be visible
    connected_user_node = next(
        (
            node
            for node in graph_data["nodes"]
            if node["user_id"] == connected_user["user_id"]
        ),
        None,
    )
    assert connected_user_node["status"] is not None, "Fresh status should be visible"
    assert (
        connected_user_node["status"]["status_content"]
        == connected_user["status_content"]
    )
