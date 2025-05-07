from enum import Enum
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

class BookingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class BookingBase(BaseModel):
    artisan_id: PyObjectId
    service_name: str
    service_description: str
    date: datetime
    duration: float  # in hours
    location: str
    agreed_price: Optional[float] = None

class BookingCreate(BookingBase):
    pass

class BookingOut(BookingBase):
    id: PyObjectId = Field(..., alias="_id")
    client_id: PyObjectId
    status: BookingStatus
    payment_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        use_enum_values = True

class BookingUpdate(BaseModel):
    service_name: Optional[str] = None
    service_description: Optional[str] = None
    date: Optional[datetime] = None
    duration: Optional[float] = None
    location: Optional[str] = None
    agreed_price: Optional[float] = None
    status: Optional[BookingStatus] = None