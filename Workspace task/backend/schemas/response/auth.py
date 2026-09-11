from pydantic import BaseModel , field_validator , ConfigDict

class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token : str
    token_type : str

    @field_validator("access_token")
    @classmethod
    def access_token_format(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Access token cannot be empty")
        return v

    @field_validator("token_type")
    @classmethod
    def token_type_validator(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("token type cannot be empty")
        if v != "bearer":
            raise ValueError("token typer must be bearer")
        return v