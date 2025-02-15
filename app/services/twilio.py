"""This file manages all the Twilio Services"""

# external
from fastapi import Request
from twilio.rest import Client
from functools import lru_cache
# internal
from app.core.config import settings
from app.schemas.twilio import TwilioVerificationModel, VerifyOTPModel
from app.schemas.users import UserPhonenumber

@lru_cache
def get_twilio_client(request: Request) -> Client:
    """returns a shared twilio client"""

    return request.app.state.twilio_client

@lru_cache
def get_twilio_service(request: Request):
    """Return the connect3 service. No dependency injection needed since we only have one service and there's no need to OOP this"""
    return request.app.state.twilio_client.verify.v2.services(
        sid=settings.TWILIO_PHONEAUTH_SERVICE_SID # This is the service sid for the phone auth service
    )


def send_OTP_text(phonenumber: UserPhonenumber, service: Client) -> TwilioVerificationModel:
    """
    Sends out verification text to the given phonenumber. 
    The phone number MUST have a +1 modifier in front of it. This verification service does not add it for you.
    returns the STATUS
    """
    try: 
        verification = service.verifications.create(  
        to=str(phonenumber.phonenumber),
        channel="sms"
        )
        return TwilioVerificationModel(
        to=verification.to,
        channel=verification.channel,
        status=verification.status,
        date_created=verification.date_created,
        date_updated=verification.date_updated
    )
    except Exception as e:
        print(str(e))
        raise Exception(e)

def verify_OTP_text(verification_code: VerifyOTPModel, service: Client) -> TwilioVerificationModel:
    """
    Verifies the OTP for a given phone number.
    the phone number MUST have the +1 modifier in front of it. This verification service does not add it for you
    """
    verification_check = service.verification_checks.create(  # Removed await, as this is a synchronous call
        to=str(verification_code.phonenumber),
        code=verification_code.code
    )
    return TwilioVerificationModel(
        to=verification_check.to,
        channel=verification_check.channel,
        status=verification_check.status,
        date_created=verification_check.date_created,
        date_updated=verification_check.date_updated
    )







