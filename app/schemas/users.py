from pydantic import BaseModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import List

# internal
from app.schemas.auth import Token
from app.schemas.usphonenumber import USPhoneNumber

# PhoneNumber Type SETS THE DEFAULT TYPE TO BE OF US and the formating!!
PhoneNumber.default_region_code = "US"
PhoneNumber.phone_format = "E164"
class BaseUser(BaseModel):
    # base model for users 
    name: str
    phonenumber: USPhoneNumber
    hashed_password: str

class UserPhonenumber(BaseModel):
    """Just a User's phonenumber"""
    phonenumber: USPhoneNumber

class SignUpUser(BaseModel):
    """Schema for a user who is signing up"""
    name: str
    phonenumber: USPhoneNumber
    password: str

class SignUpUserWithToken(BaseModel):
    """Schema for a user who is signing up with a verified token"""
    user: SignUpUser
    phone_verification_token: Token

class LogInUser(BaseModel):
    """Schema for a user who is loggin in """
    phonenumber: USPhoneNumber
    password: str

class UserInDb(BaseModel):
    # model for users in the database
    user_id: str
    name: str
    phonenumber: USPhoneNumber
    hashed_password: str
    created_at: str
    remaining_connections: int

class MinimalUser(BaseModel):
    """A minimal user model that only gives name and phone number"""
    name: str
    phonenumber: USPhoneNumber

class UserConnections(BaseModel):
    """Model that describes the connections, and number of connections that a user currently has in the DB"""
    connections: List[MinimalUser] = Field(default_factory=list)

    @property
    def num_connections(self) -> int:
        return len(self.connections)
    
    @classmethod
    def from_nodes(cls, nodes: List) -> "UserConnections":
        """
        Creates a UserConnections instance from a list of node objects.
        
        Each node is assumed to be convertible to a dictionary of properties
        that match the fields required by MinimalUser.
        """
        connections = [MinimalUser(**dict(node)) for node in nodes]
        return cls(connections=connections)

