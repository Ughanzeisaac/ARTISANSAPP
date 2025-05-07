from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId
from .client import PyObjectId

class ArtisanBase(BaseModel):
    name: str
    email: str
    profession: str
    skills: List[str]
    location: str
    description: str
    hourly_rate: Optional[float] = None
    availability: dict = {}
    profile_picture: Optional[str] = None
    rating: float = 0.0
    review_count: int = 0

class ArtisanInDB(ArtisanBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}