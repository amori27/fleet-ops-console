import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.action import ActionStatus


class ActionCreate(BaseModel):
    action_type: str
    payload: dict = Field(default_factory=dict)
    idempotency_key: str = Field(
        ..., alias="Idempotency-Key", description="Client-supplied idempotency key"
    )


class ActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_id: uuid.UUID
    action_type: str
    payload: dict
    status: ActionStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
