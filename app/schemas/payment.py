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

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentBase(BaseModel):
    booking_id: PyObjectId
    amount: float
    method: PaymentMethod
    currency: str = "USD"

class PaymentCreate(PaymentBase):
    token: str  

class PaymentOut(PaymentBase):
    id: PyObjectId = Field(..., alias="_id")
    client_id: PyObjectId
    artisan_id: PyObjectId
    status: PaymentStatus
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        use_enum_values = True