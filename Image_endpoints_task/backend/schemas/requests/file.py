from pydantic import BaseModel ,field_validator
from backend.models.file import FileCategory

class FileUploadRequest(BaseModel):
    category: FileCategory

    @field_validator("category")
    @classmethod
    def validate_category(cls,v:FileCategory)->FileCategory:
        if isinstance(v,str):
            v = v.strip().lower()
            if not v:
                raise ValueError("File category cannot be empty")
            valid_categories = {item.value for item in FileCategory}
            if v not in valid_categories:
                raise ValueError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        return v
    