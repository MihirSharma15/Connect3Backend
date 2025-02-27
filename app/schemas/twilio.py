from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

from app.schemas.auth import Token
from app.schemas.usphonenumber import USPhoneNumber

class TwilioVerificationModel(BaseModel):
    """
    Schema that represents the schema of the service after you send the OTP or verify an OTP.
    the status will either be pending or approved
    """
    to: USPhoneNumber
    channel: str
    status: Literal["pending", "approved", "canceled", "max_attemps_reached", "deleted", "failed", "expired"]
    date_created: datetime
    date_updated: datetime
    phone_verification_token: Optional[Token] = None


class VerifyOTPModel(BaseModel):
    """This model is used to verify the OTP code from a given phone number. Used during authentication practices"""
    phonenumber: USPhoneNumber
    code: str


