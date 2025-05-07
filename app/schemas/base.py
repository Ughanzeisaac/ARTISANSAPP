# app/schemas/base.py
from pydantic import BaseModel
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

class BaseSchema(BaseModel):
    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}