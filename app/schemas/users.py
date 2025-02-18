from pydantic import BaseModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import List, Optional, Union

# internal
from app.schemas.auth import Token
from app.schemas.usphonenumber import USPhoneNumber
class BaseUser(BaseModel):
    # base model for users
    name: Optional[str] = str
    phonenumber: USPhoneNumber
    hashed_password: Optional[str] = str

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
    """model for users in the database"""
    user_id: str
    name: str
    phonenumber: USPhoneNumber
    hashed_password: str
    created_at: str
    remaining_connections: int
    is_verified: bool 

class MinimalUser(BaseModel):
    """A minimal user model that only gives name and phone number"""
    user_id: str
    name: str
    phonenumber: Union[USPhoneNumber, str] # change this so USPHonenumber in prod.

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

class GraphEdge(BaseModel):
    """Model that describes the edge between two users in the DB"""
    source: str #ID of the starting Node
    target: str #ID of the ending Node

class GraphResponse(BaseModel):
    """Model that describes the response of the graph query"""
    nodes: List[MinimalUser] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)