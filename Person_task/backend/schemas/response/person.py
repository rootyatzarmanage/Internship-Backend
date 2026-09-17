import uuid
from datetime import datetime
from pydantic import BaseModel,ConfigDict

class PersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id : uuid.UUID
    name : str 
    age : int 
    created_at : datetime
    updated_at : datetime

