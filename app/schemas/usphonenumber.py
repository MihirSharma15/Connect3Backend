"""
This file represents the schema for the phone number for this application. If you need to use a phone number, 
use this phone number.
"""

# custom_types.py
from pydantic_extra_types.phone_numbers import PhoneNumber as BasePhoneNumber

class USPhoneNumber(BasePhoneNumber):
    default_region_code = "US"
    phone_format = "E164"