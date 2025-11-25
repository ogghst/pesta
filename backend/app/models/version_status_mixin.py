"""Version, entity tracking, and status mixin for all entities."""

import uuid

from sqlmodel import Field, SQLModel


class VersionStatusMixin(SQLModel):
    """Base mixin providing entity_id, version, and status fields.

    Fields:
        entity_id: Stable identifier shared across all versions of the same entity
        version: Sequential version number (per entity and branch if applicable)
        status: Lifecycle state (active, deleted, merged)
    """

    entity_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        nullable=False,
        index=True,
        description="Stable identifier for logical entity",
    )
    version: int = Field(default=1, nullable=False)
    status: str = Field(default="active", max_length=20, nullable=False)
