from fastapi import HTTPException, status
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from neo4j import Session
from datetime import timedelta, datetime
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

# internal
from app.core.config import settings
from app.services.neo4j_db import create_user_in_db, get_neo4j_session, get_user_in_db
from app.schemas.users import BaseUser, SignUpUser, UserPhonenumber
from app.schemas.auth import Token, TokenData

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    """ Create an JWT token with a set expiration time"""

    to_encode = data.copy()

    expire = datetime.now() + timedelta(ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_password_hash(password: str):
    """ Get the hashed password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Compares the plain password and the hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def verify_phone_verification_token(token: Token, phonenumber: UserPhonenumber):
    """Checks if a token is valid for a given phone number by decoding it"""
    valid_token = jwt.decode(token.access_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    print("valid_token:")
    print(valid_token)
    if valid_token.get("sub") == phonenumber.phonenumber:
        return True
    return False

async def authenticate_user(phonenumber: str, password: str, session: Session):
    """Determines if the user is valid or not based on the phone number"""
    user = await get_user_in_db(phonenumber=phonenumber, session=session)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_neo4j_session)]):
    "Gets the current user"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phonenumber: str = payload.get("sub")
        if phonenumber is None:
            raise credentials_exception
        token_data = TokenData(phonenumber=phonenumber)
    except InvalidTokenError:
        raise credentials_exception
    
    user = await get_user_in_db(phonenumber=phonenumber, session=session)
    if user is None:
        raise credentials_exception

    return user

    
async def signup_user_service(user: SignUpUser, session: Session):
    """
    Signs up a user
    Checks if they exist, if they exist, raises an error
    if not, calls neo4j_db to create the user
    Returns the user
    """
    # checks if the phone number is already in use in the DB, if it is, throw an Error
    existing_user = await get_user_in_db(phonenumber=user.phonenumber, session=session)
    if existing_user:
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="A user with this phone number already exists."
        )

    # now we need to create the user. First we hash the password
    hashed_password = get_password_hash(user.password)
    # create the user we are going to input
    base_user = BaseUser(
        name=user.name,
        phonenumber=user.phonenumber,
        hashed_password=hashed_password
    )

    # create the user in the DB
    created_user = await create_user_in_db(user=base_user, session=session)
    # return the created user with hashed password
    return created_user