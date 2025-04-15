from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from neo4j import Session

from app.schemas.status import StatusInput
from app.schemas.users import BaseUser, UserPhonenumber
from app.services.auth import get_current_user
from app.services.neo4j_db import get_neo4j_session, update_user_status
from app.logger import get_logger

logger = get_logger(__name__)

status_router = APIRouter(prefix="/status", tags=["status"])


@status_router.post("", status_code=status.HTTP_201_CREATED)
async def update_status_route(
    status: StatusInput,
    current_user: Annotated[BaseUser, Depends(get_current_user)],
    session: Session = Depends(get_neo4j_session),
):
    """Updates the status of the current user"""
    try:
        if status.status_degree is None or status.status_degree <= 0:
            raise HTTPException(
                status_code=400, detail="Degree must be greater than 0"
            )
        user_phonenumber = UserPhonenumber(phonenumber=current_user.phonenumber)
        await update_user_status(user_phonenumber, status, session)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update status: {str(e)}"
        )


# @status_router.get(
#     "/{phonenumber}", status_code=status.HTTP_200_OK, response_model=MinimalStatus
# )
# async def get_status_route(
#     phonenumber: str,
#     session: Session = Depends(get_neo4j_session),
# ):
#     """Gets the status of a user"""
#     try:
#         user_phonenumber = UserPhonenumber(phonenumber=phonenumber)
#         return await get_user_status(user_phonenumber, session)
#     except Exception as e:
#         logger.error(f"Error getting status: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
