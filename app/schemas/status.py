"""Models for user statuses"""

from typing import Optional
from pydantic import BaseModel


class StatusInDb(BaseModel):
    """Model that describes the status of the user"""

    status_content: str
    status_degree: int
    status_created_at: str
    status_expired_at: str


class MinimalStatus(BaseModel):
    """Model used to create a status"""

    status_content: Optional[str] = None
    status_degree: Optional[int] = None
    status_created_at: Optional[str] = None


class StatusInput(BaseModel):
    """Model used to update a status"""

    status_content: Optional[str] = None
    status_degree: Optional[int] = None
