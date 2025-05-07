from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from .client import PyObjectId

class BookingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class BookingBase(BaseModel):
    client_id: PyObjectId
    artisan_id: PyObjectId
    service_name: str
    service_description: str
    date: datetime
    duration: float  
    location: str
    status: BookingStatus = BookingStatus.PENDING
    agreed_price: Optional[float] = None
    payment_status: str = "pending"

class BookingCreate(BookingBase):
    pass

class BookingInDB(BookingBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True