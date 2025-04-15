"""Generic utility functions for the API."""

from app.schemas.status import StatusInput


def generate_five_alphanumeric_code() -> str:
    """Generate a 5-character alphanumeric code."""
    import random
    import string

    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for _ in range(5))


def isStatusWithinDegree(status: StatusInput, degree: int) -> bool:
    """Check if the status is within the degree."""
    return status.status_degree <= degree
