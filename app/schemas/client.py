from pydantic import BaseModel, EmailStr, Field,ConfigDict
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from .artisan import ArtisanOut

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ClientBase(BaseModel):
    name: str
    email: str
    location: str
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )
class ClientCreate(ClientBase):
    password: str

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    profile_picture: Optional[str] = None
    password: Optional[str] = None
    notification_preferences: Optional[dict] = None

class ClientOut(ClientBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}

class ClientDashboard(BaseModel):
    upcoming_bookings: List[dict]
    past_bookings: List[dict]
    pending_payments: List[dict]
    recent_messages: List[dict]
    notifications: List[dict]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None