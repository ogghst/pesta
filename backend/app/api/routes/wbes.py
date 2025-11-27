import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_time_machine_control_date,
)
from app.models import (
    WBE,
    CostElement,
    Message,
    Project,
    WBECreate,
    WBEPublic,
    WBEsPublic,
    WBEUpdate,
)
from app.services.branch_filtering import (
    apply_branch_filters,
    get_branch_context,
    resolve_entity_by_entity_id,
)
from app.services.entity_versioning import ensure_branch_version
from app.services.merged_view_service import MergedViewService
from app.services.validation_service import (
    validate_revenue_allocation_with_merge_logic,
)
from app.services.version_service import VersionService

router = APIRouter(prefix="/wbes", tags=["wbes"])


def validate_revenue_allocation_against_project_limit(
    session: Session,
    project_id: uuid.UUID,
    new_revenue_allocation: Decimal,
    exclude_wbe_id: uuid.UUID | None = None,
) -> None:
    """
    Validate that sum of WBE revenue_allocation does not exceed project contract_value.
    Raises HTTPException(400) if validation fails.

    Args:
        session: Database session
        project_id: ID of the project to validate against
        new_revenue_allocation: The new revenue_allocation value being set
        exclude_wbe_id: WBE ID to exclude from the sum (for updates)
    """
    # Get project and its contract_value
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    # Query all WBEs for this project (excluding the one being updated if specified)
    statement = select(WBE).where(WBE.project_id == project_id)
    if exclude_wbe_id:
        statement = statement.where(WBE.wbe_id != exclude_wbe_id)

    wbes = session.exec(statement).all()

    # Sum existing revenue_allocation values
    total_revenue_allocation = sum(wbe.revenue_allocation for wbe in wbes)

    # Add new_revenue_allocation
    new_total = total_revenue_allocation + new_revenue_allocation

    # Compare against project.contract_value
    if new_total > project.contract_value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Total revenue allocation for WBEs (€{new_total:,.2f}) "
                f"exceeds project contract value (€{project.contract_value:,.2f})"
            ),
        )


def _end_of_day(control_date: date) -> datetime:
    """Return a timezone-aware datetime representing the end of the given control date."""
    return datetime.combine(control_date, time.max, tzinfo=timezone.utc)


@router.get("/", response_model=WBEsPublic)
def read_wbes(
    session: SessionDep,
    _current_user: CurrentUser,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
    skip: int = 0,
    limit: int = 100,
    project_id: uuid.UUID | None = Query(
        default=None, description="Filter by project ID"
    ),
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
    view_mode: str = Query(
        default="merged", description="View mode: 'merged' (default) or 'branch-only'"
    ),
) -> Any:
    """
    Retrieve WBEs.

    When view_mode='merged' (default), returns merged view of main + branch entities
    with change_status field indicating: 'created', 'updated', 'deleted', or 'unchanged'.

    When view_mode='branch-only', returns only entities from the specified branch
    (existing behavior).
    """
    cutoff = _end_of_day(control_date)

    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Handle merged view mode
    if view_mode == "merged" and project_id:
        # Get merged view using MergedViewService
        merged_wbes = MergedViewService.get_merged_wbes(
            session=session, project_id=project_id, branch=branch_name
        )

        # Filter by control date and apply pagination
        filtered_merged = [
            item for item in merged_wbes if item["entity"].created_at <= cutoff
        ]
        total_count = len(filtered_merged)
        paginated = filtered_merged[skip : skip + limit]

        # Convert to WBEPublic with change_status
        wbes_public = []
        for item in paginated:
            wbe = item["entity"]
            wbe_dict = {
                "entity_id": wbe.entity_id,
                "wbe_id": wbe.wbe_id,
                "project_id": wbe.project_id,
                "machine_type": wbe.machine_type,
                "serial_number": wbe.serial_number,
                "contracted_delivery_date": wbe.contracted_delivery_date,
                "revenue_allocation": wbe.revenue_allocation,
                "business_status": wbe.business_status,
                "notes": wbe.notes,
                "status": wbe.status,
                "version": wbe.version,
                "branch": wbe.branch,
                "change_status": item["change_status"],
            }
            wbes_public.append(WBEPublic.model_validate(wbe_dict))

        return WBEsPublic(data=wbes_public, count=total_count)

    # Branch-only view mode (existing behavior)
    if project_id:
        # Filter by project
        count_statement = (
            select(func.count())
            .select_from(WBE)
            .where(WBE.project_id == project_id)
            .where(WBE.created_at <= cutoff)
        )
        count_statement = apply_branch_filters(count_statement, WBE, branch=branch_name)
        count = session.exec(count_statement).one()

        statement = (
            select(WBE)
            .where(WBE.project_id == project_id)
            .where(WBE.created_at <= cutoff)
        )
        statement = apply_branch_filters(statement, WBE, branch=branch_name)
        statement = statement.order_by(WBE.created_at.asc(), WBE.wbe_id.asc())  # type: ignore[attr-defined]
        statement = statement.offset(skip).limit(limit)
    else:
        # Get all
        count_statement = (
            select(func.count()).select_from(WBE).where(WBE.created_at <= cutoff)
        )
        count_statement = apply_branch_filters(count_statement, WBE, branch=branch_name)
        count = session.exec(count_statement).one()

        statement = select(WBE).where(WBE.created_at <= cutoff)
        statement = apply_branch_filters(statement, WBE, branch=branch_name)
        statement = statement.order_by(WBE.created_at.asc(), WBE.wbe_id.asc())  # type: ignore[attr-defined]
        statement = statement.offset(skip).limit(limit)

    wbes = session.exec(statement).all()
    return WBEsPublic(data=wbes, count=count)


@router.get("/by-entity-id", response_model=WBEPublic)
def read_wbe_by_entity_id(
    session: SessionDep,
    _current_user: CurrentUser,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
    entity_id: uuid.UUID = Query(..., description="Entity ID of the WBE"),
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
    view_mode: str = Query(
        default="merged", description="View mode: 'merged' (default) or 'branch-only'"
    ),
) -> Any:
    """
    Get WBE by entity_id and branch.

    When view_mode='merged' (default), returns WBE with change_status field
    indicating its status relative to main branch.

    When view_mode='branch-only', returns WBE from specified branch only.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Handle merged view mode
    if view_mode == "merged":
        # Resolve entity to get project_id
        try:
            wbe = resolve_entity_by_entity_id(session, WBE, entity_id, branch_name)
        except ValueError:
            raise HTTPException(status_code=404, detail="WBE not found")

        if wbe.created_at > _end_of_day(control_date):
            raise HTTPException(status_code=404, detail="WBE not found")

        # Get merged view for the project
        merged_wbes = MergedViewService.get_merged_wbes(
            session=session, project_id=wbe.project_id, branch=branch_name
        )

        # Find the WBE in merged view by entity_id
        merged_item = None
        for item in merged_wbes:
            if item["entity"].entity_id == entity_id:
                merged_item = item
                break

        if not merged_item:
            raise HTTPException(status_code=404, detail="WBE not found")

        # Return with change_status
        wbe_entity = merged_item["entity"]
        wbe_dict = {
            "entity_id": wbe_entity.entity_id,
            "wbe_id": wbe_entity.wbe_id,
            "project_id": wbe_entity.project_id,
            "machine_type": wbe_entity.machine_type,
            "serial_number": wbe_entity.serial_number,
            "contracted_delivery_date": wbe_entity.contracted_delivery_date,
            "revenue_allocation": wbe_entity.revenue_allocation,
            "business_status": wbe_entity.business_status,
            "notes": wbe_entity.notes,
            "status": wbe_entity.status,
            "version": wbe_entity.version,
            "branch": wbe_entity.branch,
            "change_status": merged_item["change_status"],
        }
        return WBEPublic.model_validate(wbe_dict)

    # Branch-only view mode (existing behavior)
    # Resolve by entity_id and branch
    try:
        wbe = resolve_entity_by_entity_id(session, WBE, entity_id, branch_name)
    except ValueError:
        raise HTTPException(status_code=404, detail="WBE not found")

    if wbe.created_at > _end_of_day(control_date):
        raise HTTPException(status_code=404, detail="WBE not found")
    return wbe


@router.get("/{id}", response_model=WBEPublic)
def read_wbe(
    session: SessionDep,
    _current_user: CurrentUser,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
    id: uuid.UUID,
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
    view_mode: str = Query(
        default="merged", description="View mode: 'merged' (default) or 'branch-only'"
    ),
) -> Any:
    """
    Get WBE by primary key (for backward compatibility with URLs).

    This endpoint resolves the primary key to entity_id and then uses entity_id-based logic.
    """
    # Get WBE by primary key to find entity_id
    wbe = session.get(WBE, id)
    if not wbe or wbe.created_at > _end_of_day(control_date):
        raise HTTPException(status_code=404, detail="WBE not found")

    # Use entity_id to call the entity_id-based endpoint logic
    branch_name = branch or get_branch_context()

    # Handle merged view mode
    if view_mode == "merged":
        # Resolve entity to get project_id
        try:
            wbe_resolved = resolve_entity_by_entity_id(
                session, WBE, wbe.entity_id, branch_name
            )
        except ValueError:
            raise HTTPException(status_code=404, detail="WBE not found")

        if wbe_resolved.created_at > _end_of_day(control_date):
            raise HTTPException(status_code=404, detail="WBE not found")

        # Get merged view for the project
        merged_wbes = MergedViewService.get_merged_wbes(
            session=session, project_id=wbe_resolved.project_id, branch=branch_name
        )

        # Find the WBE in merged view by entity_id
        merged_item = None
        for item in merged_wbes:
            if item["entity"].entity_id == wbe.entity_id:
                merged_item = item
                break

        if not merged_item:
            raise HTTPException(status_code=404, detail="WBE not found")

        # Return with change_status
        wbe_entity = merged_item["entity"]
        wbe_dict = {
            "entity_id": wbe_entity.entity_id,
            "wbe_id": wbe_entity.wbe_id,
            "project_id": wbe_entity.project_id,
            "machine_type": wbe_entity.machine_type,
            "serial_number": wbe_entity.serial_number,
            "contracted_delivery_date": wbe_entity.contracted_delivery_date,
            "revenue_allocation": wbe_entity.revenue_allocation,
            "business_status": wbe_entity.business_status,
            "notes": wbe_entity.notes,
            "status": wbe_entity.status,
            "version": wbe_entity.version,
            "branch": wbe_entity.branch,
            "change_status": merged_item["change_status"],
        }
        return WBEPublic.model_validate(wbe_dict)

    # Branch-only view mode
    try:
        wbe_resolved = resolve_entity_by_entity_id(
            session, WBE, wbe.entity_id, branch_name
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="WBE not found")

    if wbe_resolved.created_at > _end_of_day(control_date):
        raise HTTPException(status_code=404, detail="WBE not found")
    return wbe_resolved


@router.post("/", response_model=WBEPublic)
def create_wbe(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    wbe_in: WBECreate,
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Any:
    """
    Create new WBE.
    """
    # Validate that project exists
    project = session.get(Project, wbe_in.project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Validate revenue_allocation does not exceed project contract_value
    # Use merge logic validation for branch operations
    validate_revenue_allocation_with_merge_logic(
        session=session,
        project_id=wbe_in.project_id,
        new_revenue_allocation=wbe_in.revenue_allocation,
        branch=branch_name,
    )

    # Create WBE with version, status, and branch
    wbe = WBE.model_validate(wbe_in)
    next_version = VersionService.get_next_version(
        session=session,
        entity_type="wbe",
        entity_id=wbe.entity_id,
        branch=branch_name,
    )
    wbe.version = next_version
    wbe.status = "active"
    wbe.branch = branch_name
    session.add(wbe)
    session.commit()
    session.refresh(wbe)
    return wbe


@router.put("/", response_model=WBEPublic)
def update_wbe(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    entity_id: uuid.UUID = Query(..., description="Entity ID of the WBE"),
    wbe_in: WBEUpdate,
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Any:
    """
    Update a WBE. Creates a new version in the specified branch.

    If entity only exists in main branch, creates a new version in the specified branch
    with the user's changes. If entity exists in the branch, performs normal version increment.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Ensure entity exists in branch (creates version 1 if only in main)
    if branch_name != "main":
        wbe = ensure_branch_version(session, WBE, entity_id, branch_name, "wbe")
    else:
        try:
            wbe = resolve_entity_by_entity_id(session, WBE, entity_id, branch_name)
        except ValueError:
            raise HTTPException(status_code=404, detail="WBE not found")

    update_dict = wbe_in.model_dump(exclude_unset=True)

    # Validate revenue_allocation if it's being updated
    if "revenue_allocation" in update_dict:
        new_revenue_allocation = update_dict["revenue_allocation"]
        validate_revenue_allocation_with_merge_logic(
            session=session,
            project_id=wbe.project_id,
            new_revenue_allocation=new_revenue_allocation,
            branch=branch_name,
            exclude_entity_id=entity_id,
        )

    # Get next version number for this entity in this branch
    next_version = VersionService.get_next_version(
        session=session,
        entity_type="wbe",
        entity_id=entity_id,
        branch=branch_name,
    )

    # Create new version: copy existing WBE and update with new values
    # Note: This preserves the old version (it remains in the database)
    new_wbe = WBE(
        entity_id=entity_id,
        project_id=wbe.project_id,
        machine_type=update_dict.get("machine_type", wbe.machine_type),
        serial_number=update_dict.get("serial_number", wbe.serial_number),
        contracted_delivery_date=update_dict.get(
            "contracted_delivery_date", wbe.contracted_delivery_date
        ),
        revenue_allocation=update_dict.get(
            "revenue_allocation", wbe.revenue_allocation
        ),
        business_status=update_dict.get("business_status", wbe.business_status),
        notes=update_dict.get("notes", wbe.notes),
        version=next_version,
        status="active",
        branch=branch_name,
    )

    session.add(new_wbe)
    session.commit()
    session.refresh(new_wbe)
    return new_wbe


@router.delete("/")
def delete_wbe(
    session: SessionDep,
    _current_user: CurrentUser,
    entity_id: uuid.UUID = Query(..., description="Entity ID of the WBE"),
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Message:
    """
    Delete a WBE (soft delete: sets status='deleted').

    If entity only exists in main branch, creates a new version in the specified branch
    with status='deleted'. If entity exists in the branch, performs normal soft delete.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Ensure entity exists in branch (creates version 1 if only in main)
    if branch_name != "main":
        wbe = ensure_branch_version(session, WBE, entity_id, branch_name, "wbe")
    else:
        try:
            wbe = resolve_entity_by_entity_id(session, WBE, entity_id, branch_name)
        except ValueError:
            raise HTTPException(status_code=404, detail="WBE not found")

    # Check if WBE has cost elements (in the same branch)
    # Need to find cost elements by wbe_id (primary key) in the branch
    ce_statement = (
        select(func.count())
        .select_from(CostElement)
        .where(CostElement.wbe_id == wbe.wbe_id)
    )
    ce_statement = apply_branch_filters(ce_statement, CostElement, branch=branch_name)
    ce_count = session.exec(ce_statement).one()

    if ce_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete WBE with {ce_count} existing cost element(s). Delete cost elements first.",
        )

    # Soft delete: create new version with status='deleted'
    next_version = VersionService.get_next_version(
        session=session,
        entity_type="wbe",
        entity_id=entity_id,
        branch=branch_name,
    )

    deleted_wbe = WBE(
        entity_id=entity_id,
        project_id=wbe.project_id,
        machine_type=wbe.machine_type,
        serial_number=wbe.serial_number,
        contracted_delivery_date=wbe.contracted_delivery_date,
        revenue_allocation=wbe.revenue_allocation,
        business_status=wbe.business_status,
        notes=wbe.notes,
        version=next_version,
        status="deleted",
        branch=branch_name,
    )

    session.add(deleted_wbe)
    session.commit()
    return Message(message="WBE deleted successfully")
