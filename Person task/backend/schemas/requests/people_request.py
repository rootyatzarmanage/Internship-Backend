from datetime import datetime
from pydantic import BaseModel,field_validator
from backend.models.person import Person

class BulkRequest(BaseModel):
    name : str
    age : int 
    @field_validator("name")
    @classmethod
    def name_format(cls,v:str)->str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v
    
    @field_validator("age")
    @classmethod
    def age_check(cls,v:int)->int:
        if v <= 0:
            raise ValueError("Age must be greater than 0")
        return v
    
class CreatePeopleRequest(BaseModel):
    people : list[BulkRequest]
