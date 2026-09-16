from pydantic import BaseModel,field_validator , ConfigDict

class BarChartData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    label : str
    value : int     

    @field_validator("label")
    @classmethod
    def label_format(cls,v : str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Label cannot be empty")
        return v

    @field_validator("value")
    @classmethod
    def value_validation(cls,v: int) -> int:
        if v < 0:
            raise ValueError("Value cannot be negative")
        return v

class BarChartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    data : list[BarChartData]

    @field_validator("data")
    @classmethod
    def data_validation(cls,v : list[BarChartData])-> list[BarChartData]:
        if not v:
            raise ValueError("Data list cannot be empty")
        return v