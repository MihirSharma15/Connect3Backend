# external 
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from neo4j import Session

# internal
from app.services.neo4j_db import check_connection, check_direct_connection, create_connection, find_shortest_path, get_neo4j_session, create_user_in_db, get_num_of_connections, get_user_graph, get_user_in_db, reduce_connection_count
from app.schemas.users import BaseUser, GraphResponse, UserConnections, UserInDb, UserPhonenumber
from app.services.auth import get_current_user

user_router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@user_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user: BaseUser, session: Session = Depends(get_neo4j_session)):
    """Creates a user given a BaseUser """
    try: 
        return await create_user_in_db(user, session)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error. Failed to create User."
        )
    
@user_router.get("/me", response_model=UserInDb)
async def get_current_user_route(current_user: Annotated[BaseUser, Depends(get_current_user)]):
    """Gets the current active user information"""
    return current_user


@user_router.post("/connect", status_code=status.HTTP_201_CREATED)
async def create_connection_route(receiver: UserPhonenumber, current_user: Annotated[BaseUser, Depends(get_current_user)], session: Session = Depends(get_neo4j_session)):
    """Creates a connection between the current user and the phone number. If the current_user has 0 remaining_connections, we throw an error. If we can't find the receiver, we throw an error. """
    curr_phonenumber = UserPhonenumber(phonenumber=current_user.phonenumber)
    remaining_connections = await get_num_of_connections(curr_phonenumber, session)
    if remaining_connections <= 0:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Cannot create connection. User has reached maximum connections."
        )
    
    receiver_user = await get_user_in_db(phonenumber=receiver.phonenumber, session=session)
    if not receiver_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create connection. Receiver user not found."
        )
    
    try:
        if await check_direct_connection(user1=current_user, user2=receiver, session=session):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create connection. Users are already directly connected."
            )
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )

    # we know the user has remaining connections and the receiver user exists, and they are not already connected
    # create the connection

    try:
        await create_connection(user1=current_user, user2=receiver, session=session)
        updated_num_of_connection = await reduce_connection_count(user1=current_user, session=session)
        return {"updated_connection": updated_num_of_connection}
    except Exception as e:
        return HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )
    
@user_router.get("/graph", status_code=status.HTTP_200_OK)
async def get_user_graph_route(current_user: Annotated[BaseUser, Depends(get_current_user)], session: Session = Depends(get_neo4j_session), degrees: int = 6) -> GraphResponse:
    """
    Returns the graph network where the current user is centered. Defaults to 6 when not provided.
    DO NOT USE MORE THAN 6 OR 7 IT WILL BREAK THE GRAPH.
    """
    try:
        current_user_phonenumber = UserPhonenumber(phonenumber=current_user.phonenumber)
        return await get_user_graph(
            user1=current_user_phonenumber,
            session=session,
            degrees=degrees
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: {str(e)}"
        )

@user_router.get("/{phonenumber}", response_model=UserInDb, status_code=status.HTTP_200_OK)
async def search_user(phonenumber: str, current_user: Annotated[BaseUser, Depends(get_current_user)], session: Session = Depends(get_neo4j_session)):
    """Searches for a user based on phone number, """
    response: UserInDb = await get_user_in_db(phonenumber=phonenumber, session=session)
    if not response:
        raise HTTPException(
            status_code=404,
            detail="User not found in DB"
        )
    
    return response
    
@user_router.get("/{phonenumber}/shortest-path", status_code=status.HTTP_200_OK)
async def get_shortest_path_to_user(phonenumber: str, current_user: Annotated[BaseUser, Depends(get_current_user)], session: Session = Depends(get_neo4j_session)) -> UserConnections:
    """Finds the shortest path to a certain user based on phone number. Returns a UserConnections model"""
    receiver=UserPhonenumber(phonenumber=phonenumber)

    try:
        return await find_shortest_path(user1=current_user, user2=receiver, session=session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Path Not Found"
        )


