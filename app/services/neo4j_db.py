"""
THIS PAGE DOCUMENTS THE NEO4J DATABASE CONNECTION

General rule of thumb, all raw cypher queries get put in here

"""

# external
from collections import deque
import datetime
import logging
from fastapi import HTTPException, Request
from neo4j import Session
from typing import Optional
from functools import lru_cache

# internal
from app.schemas.status import MinimalStatus, StatusInput
from app.schemas.users import (
    BaseUser,
    GraphEdge,
    GraphResponse,
    MinimalUser,
    MinimalUserWithStatus,
    UserConnections,
    UserInDb,
    UserPhonenumber,
)
from app.utils.utils import generate_five_alphanumeric_code

logger = logging.getLogger(__name__)


# HELPER METHODS
@lru_cache
def get_neo4j_driver(request: Request):
    """
    Get the neo4j driver from the app state
    all subsequent requests will need to have a session injected into them which will then end up being a dependency for the request handler
    """
    return request.app.state.neo4j_driver


@lru_cache
def get_neo4j_session(request: Request):
    """
    Same as above driver but returns the session instead.
    """
    return request.app.state.neo4j_session


# DB METHODS


async def create_user_in_db(user: BaseUser, session: Session) -> UserInDb:
    """
    Create or update a user in the database based on phone number.

    Removing the 'verified_user' so we just assume that all users are verified.
    """

    is_verified = True
    # Check if a user with this phone number already exists
    existing_user = await get_user_in_db(user.phonenumber, session=session)

    if existing_user:
        # User already exists and is verified, so we can't update it
        raise HTTPException(
            status_code=400, detail="User already exists and is verified"
        )
    # Create a new user node
    query = """
    CREATE (u:User {
        user_id: randomUUID(),
        name: $name,
        phonenumber: $phonenumber,
        hashed_password: $hashed_password,
        created_at: $created_at,
        remaining_connections: $remaining_connections,
        is_verified: $is_verified,
        invite_code: $invite_code,
        status_content: $status_content,
        status_degree: $status_degree,
        status_created_at: $status_created_at,
        status_expired_at: $status_expired_at
    })
    RETURN u
    """

    params = {
        "name": user.name,
        "phonenumber": str(user.phonenumber),
        "hashed_password": user.hashed_password,
        "is_verified": is_verified,
        "created_at": str(datetime.datetime.now()),
        "remaining_connections": 3,
        "invite_code": generate_five_alphanumeric_code(),
        "status_content": "",
        "status_degree": 0,
        "status_created_at": "",
        "status_expired_at": "",
    }

    result = session.run(query, **params)
    record = result.single()

    if record is None:
        raise HTTPException(
            status_code=500, detail="Failed to create/update user in DB."
        )

    node = record["u"]
    # Safely convert node properties to a UserInDb
    created_user = UserInDb(
        user_id=node["user_id"],
        name=node.get("name", ""),
        phonenumber=node["phonenumber"],
        hashed_password=node.get("hashed_password", ""),
        created_at=node.get("created_at", ""),
        remaining_connections=int(node.get("remaining_connections", 0)),
        is_verified=node.get("is_verified", False),
        invite_code=node.get("invite_code", ""),
        status=MinimalStatus(
            status_content=node.get("status_content", ""),
            status_degree=node.get("status_degree", 0),
            status_created_at=node.get("status_created_at", ""),
        ),
    )

    return created_user


async def get_user_in_db(phonenumber: str, session: Session) -> Optional[UserInDb]:
    """
    Search for a user in the Neo4j database using the provided phone number
    """
    query = """
    MATCH (u:User {phonenumber: $phonenumber})
    RETURN u
    """
    params = {"phonenumber": str(phonenumber)}
    result = session.run(query, **params)
    record = result.single()

    if record is None:
        # No user found with the given phone number.
        return None

    node = record["u"]
    found_user = UserInDb(
        user_id=node["user_id"],
        name=node["name"],
        phonenumber=node["phonenumber"],
        hashed_password=node["hashed_password"],
        created_at=node["created_at"],
        remaining_connections=node["remaining_connections"],
        is_verified=(node["is_verified"] or True),
        invite_code=(node["invite_code"] or ""),
        status=MinimalStatus(
            status_content=node["status_content"],
            status_degree=node["status_degree"],
            status_created_at=node["status_created_at"],
        ),
    )  # invite_code may not exist for all users

    return found_user


async def get_user_in_db_by_id(user_id: str, session: Session) -> Optional[UserInDb]:
    """
    Search for a user in the Neo4j database using the provided user_id
    """
    query = """
    MATCH (u:User {user_id: $user_id})
    RETURN u
    """
    params = {"user_id": str(user_id)}
    result = session.run(query, **params)
    record = result.single()

    if record is None:
        # No user found with the given user_id.
        return None

    node = record["u"]
    found_user = UserInDb(
        user_id=node["user_id"],
        name=node["name"],
        phonenumber=node["phonenumber"],
        hashed_password=node["hashed_password"],
        created_at=node["created_at"],
        remaining_connections=node["remaining_connections"],
        is_verified=node["is_verified"] or True,
        invite_code=node["invite_code"] or "",
        status=MinimalStatus(
            status_content=(node["status_content"] or ""),
            status_degree=(node["status_degree"] or ""),
            status_created_at=(node["status_created_at"] or ""),
        ),
    )  # invite_code may not exist for all users

    return found_user


async def find_user_by_invite_code(
    invite_code: str, session: Session
) -> Optional[UserInDb]:
    """
    Search for a user in the Neo4j database given a 'invite code'
    :param invite_code: the invite code of the user to find
    :param session: an active neo4j session
    :return: a UserInDb object if found, otherwise None
    """
    if not invite_code or invite_code == "":
        return None

    query = """
    MATCH (u:User {invite_code: $invite_code})
    RETURN u
    """
    params = {"invite_code": str(invite_code)}
    result = session.run(query, **params)
    record = result.single()

    if record is None:
        # No user found with the given phone number.
        return None

    node = record["u"]
    found_user = UserInDb(
        user_id=node["user_id"],
        name=node["name"],
        phonenumber=node["phonenumber"],
        hashed_password=node["hashed_password"],
        created_at=node["created_at"],
        remaining_connections=node["remaining_connections"],
        is_verified=node["is_verified"] or True,
        invite_code=node["invite_code"] or "",
        status=MinimalStatus(
            status_content=(node["status_content"] or ""),
            status_degree=(node["status_degree"] or ""),
            status_created_at=(node["status_created_at"] or ""),
        ),
    )  # invite_code may not exist for all users

    return found_user


async def check_connection(
    user1: UserPhonenumber, user2: UserPhonenumber, session: Session
) -> bool:
    """
    Checks if two users are connected by ANY PATH.
    user1 and user2 are both UserPhoneNumbers
    """
    query = """
    MATCH (u1:User {phonenumber: $phone1}), (u2:User {phonenumber: $phone2})
    OPTIONAL MATCH p = shortestPath((u1)-[:FRIENDS_WITH*]-(u2))
    WITH p IS NOT NULL AS isConnected
    RETURN isConnected
    """
    if user1.phonenumber == user2.phonenumber:
        raise ValueError

    # Extract phonenumber from each BaseUser
    try:
        phone1 = user1.phonenumber
        phone2 = user2.phonenumber
        result = session.run(query, phone1=phone1, phone2=phone2)
        record = result.single()
        if record:
            return bool(record["isConnected"])

        # If there's no record, consider them not connected
        return False
    except ValueError as e:
        raise ValueError(e) from e


async def check_direct_connection(
    user1: UserPhonenumber, user2: UserPhonenumber, session: Session
) -> bool:
    """
    Checks if two users are connected DIRECTLY aka A->B.
    user1 and user2 are both UserPhoneNumbers
    """
    query = """
    MATCH (u1:User {phonenumber: $phone1}), (u2:User {phonenumber: $phone2})
    OPTIONAL MATCH (u1)-[r:FRIENDS_WITH]->(u2)
    WITH r IS NOT NULL AS isConnected
    RETURN isConnected
    """
    if user1.phonenumber == user2.phonenumber:
        raise ValueError

    # Extract phonenumber from each BaseUser
    try:
        phone1 = user1.phonenumber
        phone2 = user2.phonenumber
        result = session.run(query, phone1=phone1, phone2=phone2)
        record = result.single()
        if record:
            return bool(record["isConnected"])

        # If there's no record, consider them not connected
        return False
    except ValueError as e:
        raise ValueError(e) from e


async def create_connection(
    user1: UserPhonenumber, user2: UserPhonenumber, session: Session
):
    """
    Checks if there's any existing path between user1 and user2.
    If no path exists, creates a FRIENDS_WITH relationship.
    User1 is considered to be the sender, and user2 is the receiver
    we subtract -1 from the user1

    Returns:
        bool: True if a new relationship was created, False if already connected.
    """

    # checks that the two user1 and user2 are not the same
    if user1.phonenumber == user2.phonenumber:
        raise ValueError

    # 1. Check if there's a direct path between them
    if not await check_direct_connection(user1, user2, session):
        # 2. No existing connection found, so create a new one
        query = """
        MATCH (u1:User {phonenumber: $phone1}), (u2:User {phonenumber: $phone2})
        MERGE (u1)-[:FRIENDS_WITH]->(u2)
        MERGE (u2)-[:FRIENDS_WITH]->(u1)
        RETURN u1, u2
        """
        session.run(query, phone1=user1.phonenumber, phone2=user2.phonenumber)
        return True  # indicates a new relationship was created

    # Already connected, do nothing
    return False


async def get_connections(user1: UserPhonenumber, session: Session) -> UserConnections:
    """Returns a UserConnections model which represents all of a user1's direct connections as well as number of connections"""
    query = """
    MATCH (u:User { phonenumber: $phone })-[:FRIENDS_WITH]->(c:User)
    RETURN collect(c) AS connections
    """
    result = session.run(query=query, phone=user1.phonenumber)
    record = result.single()

    if record is None:
        return UserConnections(connections=[])

    connection_nodes = record["connections"] or []
    connections_list = []
    for node in connection_nodes:
        connections_list.append(
            MinimalUser(
                id=node["user_id"],
                name=node["name"],
                phonenumber=node["phonenumber"],
                remaining_connections=node["remaining_connections"],
            )
        )
    return UserConnections(connections=connections_list)


async def get_num_of_connections(user1: UserPhonenumber, session: Session) -> int:
    """Gets remaining_connections of a user"""

    user = await get_user_in_db(user1.phonenumber, session=session)
    if not user:
        # couldn't find the user
        return ValueError

    return user.remaining_connections


async def reduce_connection_count(user1: UserPhonenumber, session: Session):
    """Reduce the connection count by 1 of a user"""
    current_count = await get_num_of_connections(user1=user1, session=session)
    if current_count <= 0:
        raise ValueError

    query_update = """
    MATCH (u:User {phonenumber: $phone})
    SET u.remaining_connections = u.remaining_connections - 1
    RETURN u.remaining_connections AS updated_rc
    """
    update_result = session.run(query_update, phone=user1.phonenumber)
    update_record = update_result.single()
    # Optionally return the new value, or just return None if you don't need it
    return update_record["updated_rc"]


async def find_shortest_path(
    user1: UserPhonenumber, user2: UserPhonenumber, session: Session
) -> UserConnections:
    """Finds the shortest path between two users and returns a list of all users in between. Returns a UserConnections class"""

    query = """
    MATCH (u1:User {phonenumber: $user1_phonenumber}),
          (u2:User {phonenumber: $user2_phonenumber})
    MATCH path = shortestPath((u1)-[:FRIENDS_WITH*]-(u2))
    RETURN nodes(path) AS userConnections
    """
    result = session.run(
        query,
        user1_phonenumber=user1.phonenumber,
        user2_phonenumber=user2.phonenumber,
    )
    record = result.single()
    if record:
        # Process the record to convert it into your UserConnections class.
        nodes = record["userConnections"]

        # transforms into a list of Minimal Users
        return UserConnections.from_nodes(nodes)
    else:
        # Handle the case when no path is found
        raise ValueError("No connection path found between the two users.")


async def get_user_graph(
    user1: UserPhonenumber, session: Session, degrees: int = 6
) -> GraphResponse:
    """
    Retrieves a user's graph up to the specified degree.
    This version uses APOC to fetch the full subgraph (nodes and relationships)
    and computes each node's degree (shortest distance from the starting user)
    using a BFS in Python.
    """
    degrees_int = int(degrees)
    if degrees_int < 1:
        raise ValueError("Degrees must be at least 1.")

    # Ensure fast lookup by using an index on phonenumber.
    current_user = await get_user_in_db(user1.phonenumber, session)
    if not current_user:
        raise ValueError("Current user not found")

    # Fetch the full subgraph (nodes and relationships) using APOC.
    # Note: Ensure APOC is installed and enabled in your Neo4j instance.
    query = """
    MATCH (u:User {phonenumber: $phone})
    CALL apoc.path.subgraphAll(u, {
        relationshipFilter: "FRIENDS_WITH",
        maxLevel: $maxLevel
    }) YIELD nodes, relationships
    RETURN nodes, relationships
    """
    result = session.run(query, phone=user1.phonenumber, maxLevel=degrees_int)
    record = result.single()
    if record is None:
        return GraphResponse(nodes=[], edges=[])

    nodes_raw = record["nodes"]
    relationships_raw = record["relationships"]
    logger.info(f"Nodes: {nodes_raw}")
    logger.info(f"Relationships: {relationships_raw}")

    # Build a dictionary of nodes keyed by their unique user_id.
    # Also initialize each node's degree to None (to be computed below) and override phonenumber.
    node_dict = {}
    for node in nodes_raw:
        user_id = node.get("user_id")
        if user_id is None:
            continue
        node_data = dict(node)
        node_data["degree"] = None  # Will be updated via BFS.
        node_data["phonenumber"] = None  # Hide the phone if required.
        node_dict[user_id] = MinimalUserWithStatus(
            user_id=node_data["user_id"],
            name=node_data["name"],
            phonenumber=node_data["phonenumber"],
            remaining_connections=node_data["remaining_connections"],
            status=MinimalStatus(
                status_content=(node_data["status_content"] or ""),
                status_degree=(node_data["status_degree"] or 0),
                status_created_at=(node_data["status_created_at"] or ""),
            ),
        )

    # Create an undirected graph (adjacency list) from the relationships.
    # This ensures that every edge is considered when computing degrees.
    graph_adj = {node_id: set() for node_id in node_dict}
    for rel in relationships_raw:
        src = rel.start_node.get("user_id")
        tgt = rel.end_node.get("user_id")
        # Only add relationships if both endpoints exist in our node_dict.
        if src in node_dict and tgt in node_dict:
            graph_adj[src].add(tgt)
            graph_adj[tgt].add(src)

    # Use BFS to compute the degree (shortest distance) for each node.
    start_node_id = current_user.user_id
    queue = deque([(start_node_id, 0)])
    visited = set()
    while queue:
        current, dist = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        # If the node is present in our dictionary, update its degree.
        if current in node_dict:
            node_dict[current].degree = dist
        # Enqueue all unvisited neighbors with an incremented distance.
        for neighbor in graph_adj.get(current, []):
            if neighbor not in visited:
                queue.append((neighbor, dist + 1))

    # Process relationships to build the list of edges.
    # We add an edge only if both endpoints are in our processed node dictionary.
    edges_set = set()
    for rel in relationships_raw:
        src = rel.start_node.get("user_id")
        tgt = rel.end_node.get("user_id")
        if src in node_dict and tgt in node_dict:
            edges_set.add((src, tgt))

    edges = [GraphEdge(source=src, target=tgt) for src, tgt in edges_set]

    return GraphResponse(nodes=list(node_dict.values()), edges=edges)


async def get_user_status(user: UserPhonenumber, session: Session) -> MinimalStatus:
    """Gets the status of a user in the db"""
    query = """
    MATCH (u:User {phonenumber: $phone})
    RETURN u.status_content, u.status_degree, u.status_created_at
    """
    try:
        result = session.run(query=query, phone=user.phonenumber)
        record = result.single()
        if not record:
            raise ValueError("User not found")
        return MinimalStatus(
            status_content=record["status_content"],
            status_degree=record["status_degree"],
            status_created_at=record["status_created_at"],
        )
    except ValueError:
        raise


async def update_user_status(
    user: UserPhonenumber, status: StatusInput, session: Session
) -> None:
    """Updates the status of a user in the db"""
    query = """
    MATCH (u:User {phonenumber: $phone})
    SET u.status_content = $status_content,
        u.status_degree = $status_degree,
        u.status_created_at = $status_created_at,
        u.status_expired_at = $status_expired_at
    RETURN u
    """

    try:
        result = session.run(
            query=query,
            phone=user.phonenumber,
            status_content=status.status_content,
            status_degree=status.status_degree,
            status_created_at=str(datetime.datetime.now()),
            status_expired_at=str(datetime.datetime.now() + datetime.timedelta(days=1)),
        )

        record = result.single()
        if not record:
            raise ValueError("User not found")

    except Exception as e:
        raise ValueError(f"Failed to update status: {str(e)}")
