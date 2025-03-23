"""
This file represents the schema for the phone number for this application. If you need to use a phone number, 
use this phone number.
"""

import re
from pydantic import BaseModel
from pydantic_core import core_schema

US_PHONE_REGEX = re.compile(r'^\+1\d{10}$')
class USPhoneNumber(str):
    default_region_code = "US"
    phone_format = "E164"

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        # 1. Create a string schema with our simple regex pattern.
        str_schema = core_schema.str_schema(pattern=US_PHONE_REGEX.pattern)
        # 2. Wrap that schema so the final result is an instance of USPhoneNumber
        return core_schema.no_info_after_validator_function(cls, str_schema)