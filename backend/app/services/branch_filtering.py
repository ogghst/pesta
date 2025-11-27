"""Branch and status filtering utilities for query scoping.

This module provides utilities to automatically filter queries by branch (for WBE/CostElement)
and status (for all entities) to ensure only active records in the correct branch are returned.

The filtering follows the same pattern as time_machine.py for consistency.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.sql.selectable import Select
from sqlmodel import Session, SQLModel, select

from app.models import BranchVersionMixin, VersionStatusMixin

# Context variable for current branch (thread-safe)
_branch_context: ContextVar[str] = ContextVar("branch_context", default="main")

# Type variable for SQLModel subclasses
T = TypeVar("T", bound=SQLModel)


def get_branch_context() -> str:
    """Get the current branch context.

    Returns:
        Current branch name (default: 'main')
    """
    return _branch_context.get()


def set_branch_context(branch: str) -> None:
    """Set the current branch context.

    Args:
        branch: Branch name to set (e.g., 'main', 'co-001')
    """
    _branch_context.set(branch)


def apply_branch_filters(
    statement: Select[Any],
    model_class: type[T],
    branch: str | None = None,
    status: str = "active",
    include_deleted: bool = False,
) -> Select[Any]:
    """Apply branch and status filters to a query for branch-enabled entities (WBE, CostElement).

    This function adds filters for:
    - branch (defaults to current branch context or 'main')
    - status (defaults to 'active', can include 'deleted' if include_deleted=True)

    Args:
        statement: SQLAlchemy Select statement to filter
        model_class: Model class (must be WBE or CostElement)
        branch: Branch name to filter by (defaults to current branch context or 'main')
        status: Status to filter by (default: 'active')
        include_deleted: If True, include deleted records (status='deleted')

    Returns:
        Filtered Select statement

    Raises:
        ValueError: If model_class is not WBE or CostElement
    """
    if not issubclass(model_class, BranchVersionMixin):
        raise ValueError(
            f"apply_branch_filters can only be used with branch-enabled models (WBE, CostElement), got {model_class.__name__}"
        )

    # Determine branch to use
    if branch is None:
        branch = get_branch_context()

    # Apply branch filter
    if hasattr(model_class, "branch"):
        statement = statement.where(model_class.branch == branch)  # type: ignore[attr-defined]

    # Apply status filter
    if hasattr(model_class, "status"):
        if include_deleted:
            # Include both active and deleted
            statement = statement.where(
                model_class.status.in_(["active", "deleted"])  # type: ignore[attr-defined]
            )
        else:
            # Only active
            statement = statement.where(model_class.status == status)  # type: ignore[attr-defined]

    return statement


def apply_status_filters(
    statement: Select[Any],
    model_class: type[T],
    status: str = "active",
    include_deleted: bool = False,
) -> Select[Any]:
    """Apply status filters to a query for version-only entities (all entities except WBE/CostElement).

    This function adds filters for:
    - status (defaults to 'active', can include 'deleted' if include_deleted=True)

    Args:
        statement: SQLAlchemy Select statement to filter
        model_class: Model class (must have VersionStatusMixin)
        status: Status to filter by (default: 'active')
        include_deleted: If True, include deleted records (status='deleted')

    Returns:
        Filtered Select statement

    Raises:
        ValueError: If model_class does not have VersionStatusMixin
    """
    if not issubclass(model_class, VersionStatusMixin):
        raise ValueError(
            f"apply_status_filters can only be used with models that have VersionStatusMixin, got {model_class.__name__}"
        )

    # Skip if model is branch-enabled (should use apply_branch_filters instead)
    if issubclass(model_class, BranchVersionMixin):
        raise ValueError(
            "apply_status_filters should not be used with branch-enabled models (WBE, CostElement). Use apply_branch_filters instead."
        )

    # Apply status filter
    if hasattr(model_class, "status"):
        if include_deleted:
            # Include both active and deleted
            statement = statement.where(
                model_class.status.in_(["active", "deleted"])  # type: ignore[attr-defined]
            )
        else:
            # Only active
            statement = statement.where(model_class.status == status)  # type: ignore[attr-defined]

    return statement


def get_active_entities_query(
    model_class: type[T],
    branch: str | None = None,
    include_deleted: bool = False,
) -> Select[Any]:
    """Get a query for active entities with appropriate filtering.

    This is a convenience function that automatically applies the correct filters
    based on whether the model is branch-enabled or not.

    Args:
        model_class: Model class to query
        branch: Branch name (only used for branch-enabled models, defaults to current context)
        include_deleted: If True, include deleted records

    Returns:
        Filtered Select statement
    """
    from sqlmodel import select

    statement = select(model_class)

    # Apply appropriate filters based on model type
    if issubclass(model_class, BranchVersionMixin):
        return apply_branch_filters(
            statement, model_class, branch=branch, include_deleted=include_deleted
        )
    elif issubclass(model_class, VersionStatusMixin):
        return apply_status_filters(
            statement, model_class, include_deleted=include_deleted
        )
    else:
        # Model doesn't have versioning, return as-is
        return statement


def resolve_entity_by_entity_id(
    session: Session,
    model_class: type[T],
    entity_id: UUID | str,
    branch: str | None = None,
) -> T:
    """Resolve an entity by entity_id and branch, returning the latest active version.

    This function:
    1. Looks for the entity in the specified branch (or current branch context)
    2. If not found and branch != 'main', falls back to 'main' branch
    3. Returns the latest active version (highest version number)
    4. Raises ValueError if entity not found in any branch

    Args:
        session: Database session
        model_class: Model class (must be branch-enabled: WBE or CostElement)
        entity_id: Entity ID (UUID)
        branch: Branch name (defaults to current branch context or 'main')

    Returns:
        Latest active version of the entity

    Raises:
        ValueError: If model_class is not branch-enabled or entity not found
    """
    if not issubclass(model_class, BranchVersionMixin):
        raise ValueError(
            f"resolve_entity_by_entity_id can only be used with branch-enabled models (WBE, CostElement), got {model_class.__name__}"
        )

    # Convert entity_id to UUID if needed
    if isinstance(entity_id, str):
        entity_id = UUID(entity_id)

    # Determine branch to use
    if branch is None:
        branch = get_branch_context()

    # Get latest version in specified branch
    # Use subquery to get max version per entity_id, then join to get full record
    subquery = (
        select(
            model_class.entity_id, func.max(model_class.version).label("max_version")
        )  # type: ignore[attr-defined]
        .where(model_class.entity_id == entity_id)  # type: ignore[attr-defined]
        .where(model_class.branch == branch)  # type: ignore[attr-defined]
        .where(model_class.status == "active")  # type: ignore[attr-defined]
        .group_by(model_class.entity_id)  # type: ignore[attr-defined]
    ).subquery()

    query = (
        select(model_class)
        .join(
            subquery,
            (model_class.entity_id == subquery.c.entity_id)  # type: ignore[attr-defined]
            & (model_class.version == subquery.c.max_version),
        )
        .where(model_class.branch == branch)  # type: ignore[attr-defined]
        .where(model_class.status == "active")  # type: ignore[attr-defined]
    )

    entity = session.exec(query).first()

    # If not found in specified branch and branch != 'main', try main branch
    if entity is None and branch != "main":
        main_subquery = (
            select(
                model_class.entity_id,
                func.max(model_class.version).label("max_version"),
            )  # type: ignore[attr-defined]
            .where(model_class.entity_id == entity_id)  # type: ignore[attr-defined]
            .where(model_class.branch == "main")  # type: ignore[attr-defined]
            .where(model_class.status == "active")  # type: ignore[attr-defined]
            .group_by(model_class.entity_id)  # type: ignore[attr-defined]
        ).subquery()

        main_query = (
            select(model_class)
            .join(
                main_subquery,
                (model_class.entity_id == main_subquery.c.entity_id)  # type: ignore[attr-defined]
                & (model_class.version == main_subquery.c.max_version),
            )
            .where(model_class.branch == "main")  # type: ignore[attr-defined]
            .where(model_class.status == "active")  # type: ignore[attr-defined]
        )

        entity = session.exec(main_query).first()

    if entity is None:
        raise ValueError(
            f"{model_class.__name__} with entity_id={entity_id} not found in branch '{branch}' or 'main'"
        )

    return entity
