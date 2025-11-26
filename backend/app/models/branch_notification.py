"""Branch notification model and schemas."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class BranchNotification(SQLModel, table=True):
    """Persisted notification describing a branch event."""

    notification_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.project_id", nullable=False)
    branch: str = Field(max_length=50, nullable=False)
    event_type: str = Field(max_length=50, nullable=False)
    message: str = Field(max_length=255, nullable=False)
    recipients: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    context: dict | None = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class BranchNotificationPublic(SQLModel):
    """Public representation of a branch notification."""

    notification_id: uuid.UUID
    project_id: uuid.UUID
    branch: str
    event_type: str
    message: str
    recipients: list[str]
    context: dict | None = None
    created_at: datetime


class BranchNotificationsPublic(SQLModel):
    """Collection wrapper for branch notifications."""

    data: list[BranchNotificationPublic]
    count: int
