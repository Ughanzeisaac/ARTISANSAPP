from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

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
    email: EmailStr
    location: str
    profile_picture: Optional[str] = None
    saved_artisans: List[PyObjectId] = []
    notification_preferences: dict = {
        "email": True,
        "sms": False,
        "push": True
    }

class ClientCreate(ClientBase):
    password: str

class ClientUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    location: Optional[str]
    profile_picture: Optional[str]
    password: Optional[str]
    notification_preferences: Optional[dict]

class ClientInDB(ClientBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    email_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}