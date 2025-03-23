# tests/test_auth.py
import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app  # Ensure main.py imports and includes auth_router
import app.routes.auth as auth_module  # Import the module to patch send_OTP_text
from unittest.mock import MagicMock

from app.schemas.auth import Token
from app.schemas.users import UserPhonenumber
from app.services.auth import verify_phone_verification_token

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def test_send_code(client):
    """Test the /send-code endpoint for sending OTP codes."""
    test_phone = "+11234567890" 

    response = client.post("/auth/send-code", json={"phonenumber": test_phone})
    assert response.status_code == 201

    data = response.json()

    assert data["to"] == test_phone 
    assert data["channel"] == "sms"
    assert data["status"] == "pending"

def test_verify_code(client):
    """Tests the /verify-code endpoint for verifying OTP codes."""
    test_phone = "+11234567890"
    test_code = "123456"

    response = client.post("/auth/verify-code", json={"phonenumber": test_phone, "code": test_code})
    assert response.status_code == 202 

    data = response.json()
    logger.info(data)

    assert data["to"] == test_phone
    assert data["channel"] == "sms"
    assert data["status"] == "approved"

    # creating a Token Object 
    test_token = Token(
        access_token=data["phone_verification_token"]["access_token"],
        token_type=data["phone_verification_token"]["token_type"]
    )
    # creating a UserPhoneNumber object
    test_phonenumber = UserPhonenumber(
        phonenumber=test_phone)

    assert (verify_phone_verification_token(token=test_token, phonenumber=test_phonenumber))
    assert data["phone_verification_token"]["token_type"] == "bearer"


def test_signup_user(client):
    """Tests the /signup endpoint for signing up users."""
    test_phone = "+11234567890"
    test_name = "John Smith"
    test_code = "123456"
    test_password = "password123"

    # First send the OTP code
    client.post("/auth/send-code", json={"phonenumber": test_phone})

    # Verify the OTP code
    response = client.post("/auth/verify-code", json={"phonenumber": test_phone, "code": test_code})
    assert response.status_code == 202 

    data = response.json()
    test_token = Token(
        access_token=data["phone_verification_token"]["access_token"],
        token_type=data["phone_verification_token"]["token_type"]
    )
    # Now sign up the user
    signup_data = {
        "phonenumber": test_phone,
        "name": test_name,
        "password": test_password
    }
    headers = {"X-Phone-Verification-Token": test_token.access_token}
    
    response = client.post("/auth/signup", json=signup_data, headers=headers)
    
    assert response.status_code == 201 
    logger.info(response.json())
    user_data = response.json()
    
    assert user_data["phonenumber"] == test_phone
