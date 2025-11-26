"""Branch lock model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class BranchLock(SQLModel, table=True):
    """Represents an exclusive lock for a project branch."""

    lock_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.project_id", nullable=False)
    branch: str = Field(max_length=50, nullable=False)
    locked_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    reason: str | None = Field(default=None, max_length=200)
    locked_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
