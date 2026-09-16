import uuid
from datetime import datetime
from pydantic import BaseModel , field_validator, ConfigDict

class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id : uuid.UUID
    name : str
    category : str
    type : str
    user_id : uuid.UUID
    created_at : datetime
    updated_at : datetime
    deleted_at : datetime | None

    @field_validator("name")
    @classmethod
    def name_format(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("category")
    @classmethod
    def category_format(cls,v:str)-> str:
        v = v.strip()
        if not v:
            raise ValueError("Category cannot be empty")
        return v

    @field_validator("type")
    @classmethod
    def type_format(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Type cannot be empty")
        return v