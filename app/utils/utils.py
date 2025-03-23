"""Generic utility functions for the API."""


def generate_five_alphanumeric_code() -> str:
    """Generate a 5-character alphanumeric code."""
    import random
    import string

    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(5))