# External

from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from neo4j import Session


# internal
from app.services.auth import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, create_access_token, signup_user_service, verify_phone_verification_token
from app.schemas.users import SignUpUser, UserInDb, UserPhonenumber
from app.services.neo4j_db import get_neo4j_session
from app.schemas.auth import Token
from app.schemas.twilio import TwilioVerificationModel, VerifyOTPModel
from app.services.twilio import get_twilio_service, send_OTP_text, verify_OTP_text

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
            print("verification.to:")
            print(verification.to)
            token  = create_access_token(data={"sub": str(verification.to)})
            print("token:")
            print(token)
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
    verification_token: str = Header(..., alias="X-Phone-Verification-Token"),
    session: Session = Depends(get_neo4j_session)):
    """Route to sign up a user. First it checks if a user's token is valid with the header. If it is, it signs up the user"""
    try:
        user_phonenumber = UserPhonenumber(phonenumber=user.phonenumber)
        token_obj = Token(access_token=verification_token, token_type="bearer")
        valid_token = verify_phone_verification_token(token=token_obj, phonenumber=user_phonenumber)
        if valid_token:
            return await signup_user_service(user=user, session=session)
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid Phone Verification Token"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to Sign up user: {str(e)}"
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