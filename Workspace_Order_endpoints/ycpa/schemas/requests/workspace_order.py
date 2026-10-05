from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class WorkspaceOrderItem(BaseModel):
    workspace_id: UUID
    order_no: int = Field(
        ...,
        ge=1,
    )

class WorkspaceOrderRequest(BaseModel):
    workspaces: list[WorkspaceOrderItem]

    @model_validator(mode="after")
    def validate_unique_workspaces(self):
        workspace_ids = [
            item.workspace_id
            for item in self.workspaces
        ]
        order_numbers = [
            item.order_no
            for item in self.workspaces
        ]
        if len(workspace_ids) != len(set(workspace_ids)):
            raise ValueError(
                "Duplicate workspace IDs are not allowed"
            )
        if len(order_numbers) != len(set(order_numbers)):
            raise ValueError(
                "Duplicate order numbers are not allowed"
            )
        expected_orders = set(
            range(1, len(self.workspaces) + 1)
        )
        if set(order_numbers) != expected_orders:
            raise ValueError(
                "Order numbers must start from 1 and be sequential"
            )
        return self