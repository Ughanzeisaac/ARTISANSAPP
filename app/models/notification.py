from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId
from .client import PyObjectId,Optional

class NotificationType(str, Enum):
    BOOKING_REQUEST = "booking_request"
    BOOKING_ACCEPTED = "booking_accepted"
    BOOKING_DECLINED = "booking_declined"
    BOOKING_REMINDER = "booking_reminder"
    PAYMENT_RECEIVED = "payment_received"
    NEW_MESSAGE = "new_message"
    REVIEW_RECEIVED = "review_received"

class NotificationBase(BaseModel):
    user_id: PyObjectId
    type: NotificationType
    message: str
    related_entity_id: Optional[PyObjectId] = None 

class NotificationInDB(NotificationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True