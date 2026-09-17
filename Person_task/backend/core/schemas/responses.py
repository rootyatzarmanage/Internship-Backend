from typing import TypeVar,Generic

from pydantic import BaseModel

DataT = TypeVar("DataT")

class BaseResponse(BaseModel,Generic[DataT]):
    success : bool   = True,
    message : str | None = None,
    data : DataT | None = None,
    request_id : str |None = None

SuccessResponse = BaseResponse
