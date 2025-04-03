"""Utils file to simply Neo4j database connection and queries for testing purposes. These functions are RAW, in that they do not do any logic or validation, they simply execute the queries and return the results."""


import logging
from neo4j import Session

from app.schemas.users import UserInDb

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def util_create_user(properties: dict, session: Session) -> None:
    """Helper function to create a user node in neo4j using the provided session.
    :param properties: a dictionary of properties to set on the user node
    :param session: an active neo4j session, defaults to the client one
    """
    props_str = ", ".join(f"{key}: ${key}" for key in properties.keys())
    query = f"""
    CREATE (n:User {{
        {props_str}
    }})
    RETURN n
    """
    result = session.run(query, **properties)
    return result.single()[0]

def util_find_user_by_phonenumber(phonenumber: str, session: Session) -> UserInDb:
    """Helper function to find a user node in neo4j by phone number using the provided session.
    :param phonenumber: the phone number of the user to find
    :param session: an active neo4j session, defaults to the client one
    :return: a UserInDb object if found, otherwise None
    """
    try:
        query = """
            MATCH (u:User {phonenumber: $phonenumber})
            RETURN u
        """
        result = session.run(query, phonenumber=phonenumber)
        record = result.single()
        
        # If the query didn't match any node, return None
        if not record:
            return None
        
        node = record["u"]  # The user node

        # Build a dictionary of the node's properties
        user_data = {
            "user_id": node["user_id"],
            "name": node["name"],
            "phonenumber": node["phonenumber"],
            "hashed_password": node["hashed_password"],
            "created_at": node["created_at"],
            "remaining_connections": node["remaining_connections"],
            "is_verified": node["is_verified"],
            "invite_code": node["invite_code"]
        }
        # Construct and return the UserInDb model
        return UserInDb(**user_data)
    except Exception as e:
        logging.error("Error finding user by phonenumber %s: %s", phonenumber, e)
        return None
    
def util_find_user_by_name(name: str, session: Session) -> UserInDb:
    """Helper function to find a user node in neo4j by phone number using the provided session.
    :param phonenumber: the phone number of the user to find
    :param session: an active neo4j session, defaults to the client one
    :return: a UserInDb object if found, otherwise None
    """
    try:
        query = """
            MATCH (u:User {phonenumber: $name})
            RETURN u
        """
        result = session.run(query, name=name)
        record = result.single()
        
        # If the query didn't match any node, return None
        if not record:
            return None
        
        node = record["u"]  # The user node

        # Build a dictionary of the node's properties
        user_data = {
            "user_id": node["user_id"],
            "name": node["name"],
            "phonenumber": node["phonenumber"],
            "hashed_password": node["hashed_password"],
            "created_at": node["created_at"],
            "remaining_connections": node["remaining_connections"],
            "is_verified": node["is_verified"],
            "invite_code": node["invite_code"]
        }

        # Construct and return the UserInDb model
        return UserInDb(**user_data)
    except Exception as e:
        logging.error("Error finding user by name %s: %s", name, e)
        return None


def util_create_connection(user1: UserInDb, user2: UserInDb, session: Session) -> None:
    """Helper function to create a connection between two users in neo4j using the provided session.
    :param user1: the inviting user
    :param user2: the invited/receiving user
    NOTE: this function assumes that both users already exist in the database, and it does not do any checking to see if they have enough connections. 
    """
    try:
        query = """
        MATCH (u1:User {phonenumber: $phone1}), (u2:User {phonenumber: $phone2})
        CREATE (u1)-[rel:FRIENDS_WITH]->(u2)
        RETURN rel
        """
        result = session.run(
            query,
            phone1=user1.phonenumber,
            phone2=user2.phonenumber
        )
        
        # If Neo4j found both nodes, it will return the new relationship in result.single()
        record = result.single()
        if record is not None:
            return record["rel"]
        
        # If no record, maybe one or both users were not found
        logging.warning("Could not create connection. Possibly one of the users doesn't exist.")
        return None
        
    except Exception as e:
        logging.critical("Critical Erorr in creating connection: %s", e)

