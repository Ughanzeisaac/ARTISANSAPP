from pydantic import ConfigDict, GetJsonSchemaHandler,BaseModel
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from bson import ObjectId
from typing import Any

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, 
        _source_type: Any,
        _handler: GetJsonSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, 
        _core_schema: core_schema.CoreSchema,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {"type": "string", "format": "objectid"}
    


class ArtisanBase(BaseModel):
    name: str
    email: str
    profession: str
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )