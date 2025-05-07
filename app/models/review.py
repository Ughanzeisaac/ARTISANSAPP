from datetime import datetime
from pydantic import BaseModel, Field, conint
from bson import ObjectId
from .client import PyObjectId

class ReviewBase(BaseModel):
    booking_id: PyObjectId
    client_id: PyObjectId
    artisan_id: PyObjectId
    rating: int = Field(..., ge=1, le=5) 
    comment: str

class ReviewCreate(ReviewBase):
    pass

class ReviewInDB(ReviewBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}