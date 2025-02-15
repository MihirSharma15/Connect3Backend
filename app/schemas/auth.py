from pydantic import BaseModel

from app.schemas.usphonenumber import USPhoneNumber

class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    phonenumber: USPhoneNumber | None = None