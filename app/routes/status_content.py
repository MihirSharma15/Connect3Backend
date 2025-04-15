from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from neo4j import Session

from app.schemas.status import StatusInput
from app.schemas.users import BaseUser, UserPhonenumber
from app.services.auth import get_current_user
from app.services.neo4j_db import get_neo4j_session, update_user_status
from app.logger import get_logger

logger = get_logger(__name__)

status_router = APIRouter(prefix="/users/status", tags=["status"])


@status_router.put("/", status_code=status.HTTP_201_CREATED)
async def update_status_route(
    status: StatusInput,
    current_user: Annotated[BaseUser, Depends(get_current_user)],
    session: Session = Depends(get_neo4j_session),
):
    """Updates the status of the current user"""
    try:
        user_phonenumber = UserPhonenumber(phonenumber=current_user.phonenumber)
        await update_user_status(user_phonenumber, status, session)
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update status: {str(e)}"
        )
