"""Entity versioning utilities for CRUD operations.

This module provides helper functions for creating, updating, and soft-deleting
entities with version tracking.
"""

import uuid
from typing import Any, TypeVar

from sqlmodel import Session, SQLModel, select

from app.services.branch_filtering import apply_status_filters
from app.services.version_service import VersionService

T = TypeVar("T", bound=SQLModel)


def _resolve_identifier(
    entity: SQLModel, raw_identifier: str | uuid.UUID | None = None
) -> uuid.UUID:
    """Ensure entity has a stable identifier (entity_id)."""
    pk_column = list(entity.__class__.__table__.primary_key.columns)[0]  # type: ignore[attr-defined]
    pk_field_name = pk_column.name
    pk_value = getattr(entity, pk_field_name, None)

    identifier = getattr(entity, "entity_id", None) or raw_identifier or pk_value
    if identifier is None:
        identifier = uuid.uuid4()
    if not isinstance(identifier, uuid.UUID):
        identifier = uuid.UUID(str(identifier))
    if hasattr(entity, "entity_id"):
        entity.entity_id = identifier
    return identifier


def create_entity_with_version(
    session: Session,
    entity: T,
    entity_type: str,
    entity_id: str | None = None,
    branch: str | None = None,
) -> T:
    """Create a new entity with version=1 and status='active'.

    Args:
        session: Database session
        entity: Entity instance to create
        entity_type: Entity type name (e.g., 'project', 'user')
        entity_id: Entity ID (for version calculation, optional)
        branch: Branch name (only for branch-enabled entities)

    Returns:
        Created entity with version and status set
    """
    from app.models import BranchVersionMixin

    identifier = _resolve_identifier(entity, entity_id)
    is_branch_enabled = isinstance(entity, BranchVersionMixin)

    branch_value: str | None = branch
    if is_branch_enabled:
        branch_value = branch or getattr(entity, "branch", None) or "main"
        if hasattr(entity, "branch"):
            entity.branch = branch_value

    if identifier is not None:
        next_version = VersionService.get_next_version(
            session=session,
            entity_type=entity_type,
            entity_id=identifier,
            branch=branch_value,
        )
    else:
        next_version = 1

    # Set version and status
    if hasattr(entity, "version"):
        entity.version = next_version
    if hasattr(entity, "status"):
        entity.status = "active"

    session.add(entity)
    return entity


def update_entity_with_version(
    session: Session,
    entity_class: type[T],
    entity_id: Any,
    update_data: dict[str, Any],
    entity_type: str,
    branch: str | None = None,
) -> T:
    """Update an entity by creating a new version.

    This function:
    1. Gets the current active version
    2. Creates a new version with updated data
    3. Preserves the old version in the database

    Args:
        session: Database session
        entity_class: Entity model class
        entity_id: Entity ID (primary key)
        update_data: Dictionary of fields to update
        entity_type: Entity type name (e.g., 'project', 'user')
        branch: Branch name (only for branch-enabled entities)

    Returns:
        New version of the entity
    """
    pk_column = list(entity_class.__table__.primary_key.columns)[0]  # type: ignore[attr-defined]
    pk_field_name = pk_column.name
    pk_field = getattr(entity_class, pk_field_name)

    statement = select(entity_class).where(pk_field == entity_id)

    # Apply status filter (or branch filter for branch-enabled entities)
    from app.models import BranchVersionMixin

    is_branch_enabled = issubclass(entity_class, BranchVersionMixin)
    if is_branch_enabled:
        from app.services.branch_filtering import apply_branch_filters

        statement = apply_branch_filters(
            statement, entity_class, branch=branch or "main"
        )
    else:
        statement = apply_status_filters(statement, entity_class)

    current_entity = session.exec(statement).first()
    if not current_entity:
        raise ValueError(
            f"{entity_class.__name__} with {pk_field_name}={entity_id} not found"
        )

    identifier = getattr(current_entity, "entity_id", None) or entity_id
    next_version = VersionService.get_next_version(
        session=session,
        entity_type=entity_type,
        entity_id=identifier,
        branch=branch if is_branch_enabled else None,
    )

    if is_branch_enabled:
        entity_data = current_entity.model_dump()
        entity_data.update(update_data)
        entity_data.pop(pk_field_name, None)
        entity_data.pop("created_at", None)
        entity_data.pop("updated_at", None)
        entity_data["version"] = next_version
        entity_data["status"] = "active"
        if hasattr(entity_class, "entity_id"):
            entity_data["entity_id"] = identifier
        if hasattr(entity_class, "branch"):
            entity_data["branch"] = branch or current_entity.branch  # type: ignore[attr-defined]

        new_entity = entity_class(**entity_data)
        session.add(new_entity)
        return new_entity

    # Non-branch entities are updated in-place
    for key, value in update_data.items():
        if key in {"entity_id", pk_field_name, "version"}:
            continue
        if hasattr(current_entity, key):
            setattr(current_entity, key, value)
    if hasattr(current_entity, "version"):
        current_entity.version = next_version  # type: ignore[attr-defined]
    if hasattr(current_entity, "status"):
        current_entity.status = "active"  # type: ignore[attr-defined]

    session.add(current_entity)
    return current_entity


def soft_delete_entity(
    session: Session,
    entity_class: type[T],
    entity_id: Any,
    entity_type: str,
    branch: str | None = None,
) -> T:
    """Soft delete an entity by creating a new version with status='deleted'.

    Args:
        session: Database session
        entity_class: Entity model class
        entity_id: Entity ID (primary key)
        entity_type: Entity type name (e.g., 'project', 'user')
        branch: Branch name (only for branch-enabled entities)

    Returns:
        New version of the entity with status='deleted'
    """
    pk_column = list(entity_class.__table__.primary_key.columns)[0]  # type: ignore[attr-defined]
    pk_field_name = pk_column.name
    pk_field = getattr(entity_class, pk_field_name)

    # Get current active entity
    statement = select(entity_class).where(pk_field == entity_id)

    # Apply status filter (or branch filter for branch-enabled entities)
    from app.models import BranchVersionMixin

    is_branch_enabled = issubclass(entity_class, BranchVersionMixin)
    if is_branch_enabled:
        from app.services.branch_filtering import apply_branch_filters

        statement = apply_branch_filters(
            statement, entity_class, branch=branch or "main"
        )
    else:
        statement = apply_status_filters(statement, entity_class)

    current_entity = session.exec(statement).first()
    if not current_entity:
        raise ValueError(
            f"{entity_class.__name__} with {pk_field_name}={entity_id} not found"
        )

    identifier = getattr(current_entity, "entity_id", None) or entity_id
    next_version = VersionService.get_next_version(
        session=session,
        entity_type=entity_type,
        entity_id=identifier,
        branch=branch if is_branch_enabled else None,
    )

    if is_branch_enabled:
        entity_data = current_entity.model_dump()
        entity_data.pop(pk_field_name, None)
        entity_data.pop("created_at", None)
        entity_data.pop("updated_at", None)
        entity_data["version"] = next_version
        entity_data["status"] = "deleted"
        if hasattr(entity_class, "entity_id"):
            entity_data["entity_id"] = identifier
        if hasattr(entity_class, "branch"):
            entity_data["branch"] = branch or current_entity.branch  # type: ignore[attr-defined]

        deleted_entity = entity_class(**entity_data)
        session.add(deleted_entity)
        return deleted_entity

    # Non-branch entities: update status in place
    if hasattr(current_entity, "status"):
        current_entity.status = "deleted"  # type: ignore[attr-defined]
    if hasattr(current_entity, "version"):
        current_entity.version = next_version  # type: ignore[attr-defined]

    session.add(current_entity)
    return current_entity
