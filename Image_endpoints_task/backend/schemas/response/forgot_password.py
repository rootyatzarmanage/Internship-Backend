from pydantic import BaseModel, ConfigDict, field_validator

class ForgotPasswordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message : str
    reset_token : str

    @field_validator("message")
    @classmethod
    def message_format(cls,v:str)-> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v

    @field_validator("reset_token")
    @classmethod
    def reset_token_format(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Reset_token cannot be empty")
        return v

class ResetPasswordResponse(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_format(cls,v:str)-> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v    