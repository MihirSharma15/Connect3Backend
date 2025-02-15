"""
THIS PAGE DOCUMENTS THE NEO4J DATABASE CONNECTION

General rule of thumb, all raw cypher queries get put in here

"""
# external 
import datetime
from fastapi import HTTPException, Request
from neo4j import Session
from typing import Optional
from functools import lru_cache
# internal 
from app.schemas.users import BaseUser, MinimalUser, UserConnections, UserInDb, UserPhonenumber

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
    Create a user in the database.
    Returns the user node properties (including a newly generated user_id).
    """
    check_for_user = await get_user_in_db(user.phonenumber, session=session)
    # user already in db
    if check_for_user:
        raise ValueError
    query = """
    CREATE (u:User {
        user_id: randomUUID(),
        name: $name,
        phonenumber: $phonenumber,
        hashed_password: $hashed_password, 
        created_at: $created_at,
        remaining_connections: $remaining_connections
    })
    RETURN u
    """
    params = {
        "name": user.name,
        # Convert phone number to string in case it's stored as a specialized type
        "phonenumber": str(user.phonenumber),
        "hashed_password": user.hashed_password,
        "created_at": str(datetime.datetime.now()),
        "remaining_connections": 3
    }
    
    result = session.run(query, **params)
    record = result.single()
    if record is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user in DB."
        )
    
    node = record["u"]
    # Convert the node's properties into a dict or a Pydantic model
    created_user = UserInDb(user_id=node["user_id"], 
                            name=node["name"], 
                            phonenumber=node["phonenumber"], 
                            hashed_password=node["hashed_password"],
                            created_at=node["created_at"],
                            remaining_connections=int(node["remaining_connections"])
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
    params = {
        "phonenumber": str(phonenumber)
    }
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
        remaining_connections=node["remaining_connections"]
    )
    return found_user

async def check_connection(user1: UserPhonenumber, user2: UserPhonenumber, session: Session) -> bool:
    """
    Checks if two users are connected. 
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

async def create_connection(user1: UserPhonenumber, user2: UserPhonenumber, session: Session):
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

    # 1. Check if there's *any* path between them
    if not await check_connection(user1, user2, session):
        # 2. No existing connection found, so create a new one
        query = """
        MATCH (u1:User {phonenumber: $phone1}), (u2:User {phonenumber: $phone2})
        MERGE (u1)-[:FRIENDS_WITH]->(u2)
        MERGE (u2)-[:FRIENDS_WITH]->(u1)
        RETURN u1, u2
        """
        session.run(
            query,
            phone1=user1.phonenumber,
            phone2=user2.phonenumber
        )
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
                name=node["name"],
                phonenumber=node["phonenumber"]
            )
        )
    return UserConnections(connections=connections_list)

async def get_num_of_connections(user1: UserPhonenumber, session: Session) -> int: 
    """Gets remaining_connections of a user """

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
    # Optionally return the new value, or just return None if you don’t need it
    return update_record["updated_rc"]

async def find_shortest_path(user1: UserPhonenumber, user2: UserPhonenumber, session: Session) -> UserConnections:
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

