# External

from datetime import timedelta
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from neo4j import Session


# internal
from app.services.auth import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, create_access_token, signup_user_service, verify_phone_verification_token
from app.schemas.users import SignUpUser, UserInDb, UserPhonenumber
from app.services.neo4j_db import create_connection, find_user_by_invite_code, get_neo4j_session, get_num_of_connections, reduce_connection_count
from app.schemas.auth import Token
from app.schemas.twilio import TwilioVerificationModel, VerifyOTPModel
from app.services.twilio import get_twilio_client, get_twilio_service, send_OTP_text, send_sms, verify_OTP_text

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@auth_router.post("/send-code", response_model=TwilioVerificationModel, status_code=status.HTTP_201_CREATED)
async def send_otp_code_route(phonenumber: UserPhonenumber, twilio_service = Depends(get_twilio_service)):
    """This route sends an OTP code to the given phone number"""
    try:
        return send_OTP_text(phonenumber=phonenumber, service=twilio_service)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send OTP: {str(e)}"
        )

@auth_router.post("/verify-code", response_model=TwilioVerificationModel, status_code=status.HTTP_202_ACCEPTED)
async def verify_otp_code_route(verification_code: VerifyOTPModel, twilio_service = Depends(get_twilio_service)):
    """This route verifies the code that is being sent, and if the code is correct returns a JWT token that will be used for Signing up the user"""
    try:
        verification: TwilioVerificationModel = verify_OTP_text(verification_code=verification_code, service=twilio_service)
        if verification.status == "approved":
            token  = create_access_token(data={"sub": str(verification.to)})
            verification.phone_verification_token = Token(access_token=token, token_type="bearer")
            return verification
        else:
            return verification
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify OTP: {str(e)}"
        )

@auth_router.post("/signup", response_model=UserInDb, status_code=status.HTTP_201_CREATED)
async def signup_user_route(
    user: SignUpUser,
    invite_code: str = None,
    verification_token: str = Header(..., alias="X-Phone-Verification-Token"),
    session: Session = Depends(get_neo4j_session),
    twilio_client = Depends(get_twilio_client)):
    """Route to sign up a user. First it checks if a user's token is valid with the header. If it is, it signs up the user. Then, we determine if there is an associated invite link. If there is, then we create a connection between the two users.
    :param user: SignUpUser - The user to sign up
    :param invite_code: str - The invite code to connect the user to another user
    :param verification_token: str - The phone verification token
    :param session: Session - The neo4j session
    :param twilio_client: TwilioClient - The twilio client
    :returns UserInDb - The user that was created
    """
    try:
        user_phonenumber = UserPhonenumber(phonenumber=user.phonenumber)
        token_obj = Token(access_token=verification_token, token_type="bearer")
        valid_token = verify_phone_verification_token(token=token_obj, phonenumber=user_phonenumber)
        # check if the token is valid
        if not valid_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Phone Verification Token"
            )
        
        # if there is no invite_code, just sign the user up.
        if not invite_code:
            return await signup_user_service(user=user, session=session)

        # if there is an invite code, we want to check if the invite code is valid
        inviting_user = await find_user_by_invite_code(invite_code=invite_code, session=session)

        if not inviting_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite code is invalid."
            )
        inviting_user_phonenumber = UserPhonenumber(phonenumber=inviting_user.phonenumber)
        num_connections = await get_num_of_connections(inviting_user_phonenumber)

        if num_connections <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inviting User already reached maximum connections."
            )

        created_user = await signup_user_service(user=user, session=session)
        created_user_phonenumber = UserPhonenumber(phonenumber=created_user.phonenumber)

        # if all looks good
        await create_connection(user1=inviting_user_phonenumber, user2=created_user_phonenumber, session=session)
        await reduce_connection_count(inviting_user_phonenumber)

        # once we have created a connection between two users, we want to send an SMS to the user
        send_sms(f"{inviting_user.name} has accepted your request to join Connect3! Go to Connect3.live to see UNC's social graph expand.", to=inviting_user_phonenumber, client=twilio_client)
        return created_user
            
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Failed to Sign up user: {str(e.detail)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected Error: {str(e)}"
        )
    
@auth_router.post("/token")
async def login_for_access_token(session: Annotated[Session, Depends(get_neo4j_session)], form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = await authenticate_user(phonenumber=form_data.username, password=form_data.password, session=session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Username or Password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.phonenumber}
    )
    return Token(access_token=access_token, token_type="bearer")