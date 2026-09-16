from pydantic import BaseModel ,field_validator

class FileUploadRequest(BaseModel):
    category : str

    @field_validator("category")
    @classmethod
    def validate_category(cls,v:str)->str:
        v = v.strip()
        if not v:
            raise ValueError("File category cannot be empty")
        return v
    