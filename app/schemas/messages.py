from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
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

class MessageBase(BaseModel):
    recipient_id: PyObjectId
    content: str

class MessageCreate(MessageBase):
    pass

class MessageOut(MessageBase):
    id: PyObjectId = Field(..., alias="_id")
    sender_id: PyObjectId
    read: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}

class Conversation(BaseModel):
    participant: dict  
    last_message: dict
    unread_count: int