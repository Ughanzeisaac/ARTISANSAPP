from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from .client import PyObjectId

class MessageBase(BaseModel):
    sender_id: PyObjectId
    recipient_id: PyObjectId
    content: str
    read: bool = False

class MessageCreate(MessageBase):
    pass

class MessageInDB(MessageBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}