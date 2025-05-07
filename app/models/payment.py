from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from .client import PyObjectId,Optional

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
    client_id: PyObjectId
    artisan_id: PyObjectId
    booking_id: PyObjectId
    amount: float
    method: PaymentMethod
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentInDB(PaymentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True