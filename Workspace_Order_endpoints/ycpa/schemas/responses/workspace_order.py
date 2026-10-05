from uuid import UUID
from pydantic import BaseModel

class WorkspaceOrderItemResponse(BaseModel):
    workspace_id : UUID
    name: str
    role: str
    order_no : int

class WorkspaceOrderResponse(BaseModel):
    workspaces : list[WorkspaceOrderItemResponse]

