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
) -> Any:
    """
    Retrieve WBEs.
    """
    cutoff = _end_of_day(control_date)

    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

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


@router.get("/{id}", response_model=WBEPublic)
def read_wbe(
    session: SessionDep,
    _current_user: CurrentUser,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
    id: uuid.UUID,
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Any:
    """
    Get WBE by ID.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Query with branch and status filters
    statement = select(WBE).where(WBE.wbe_id == id)
    statement = apply_branch_filters(statement, WBE, branch=branch_name)
    wbe = session.exec(statement).first()

    if not wbe or wbe.created_at > _end_of_day(control_date):
        raise HTTPException(status_code=404, detail="WBE not found")
    return wbe


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

    # Validate revenue_allocation does not exceed project contract_value
    # Note: This validation should consider only active WBEs in the same branch
    validate_revenue_allocation_against_project_limit(
        session=session,
        project_id=wbe_in.project_id,
        new_revenue_allocation=wbe_in.revenue_allocation,
    )

    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

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


@router.put("/{id}", response_model=WBEPublic)
def update_wbe(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    id: uuid.UUID,
    wbe_in: WBEUpdate,
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Any:
    """
    Update a WBE. Creates a new version in the specified branch.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Get current active WBE in the specified branch
    statement = select(WBE).where(WBE.wbe_id == id)
    statement = apply_branch_filters(statement, WBE, branch=branch_name)
    wbe = session.exec(statement).first()

    if not wbe:
        raise HTTPException(status_code=404, detail="WBE not found")

    update_dict = wbe_in.model_dump(exclude_unset=True)

    # Validate revenue_allocation if it's being updated
    if "revenue_allocation" in update_dict:
        new_revenue_allocation = update_dict["revenue_allocation"]
        validate_revenue_allocation_against_project_limit(
            session=session,
            project_id=wbe.project_id,
            new_revenue_allocation=new_revenue_allocation,
            exclude_wbe_id=wbe.wbe_id,
        )

    # Get next version number for this entity in this branch
    next_version = VersionService.get_next_version(
        session=session,
        entity_type="wbe",
        entity_id=wbe.entity_id,
        branch=branch_name,
    )

    # Create new version: copy existing WBE and update with new values
    # Note: This preserves the old version (it remains in the database)
    new_wbe = WBE(
        entity_id=wbe.entity_id,
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


@router.delete("/{id}")
def delete_wbe(
    session: SessionDep,
    _current_user: CurrentUser,
    id: uuid.UUID,
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Message:
    """
    Delete a WBE (soft delete: sets status='deleted').
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Get current active WBE in the specified branch
    statement = select(WBE).where(WBE.wbe_id == id)
    statement = apply_branch_filters(statement, WBE, branch=branch_name)
    wbe = session.exec(statement).first()

    if not wbe:
        raise HTTPException(status_code=404, detail="WBE not found")

    # Check if WBE has cost elements (in the same branch)
    ce_statement = (
        select(func.count()).select_from(CostElement).where(CostElement.wbe_id == id)
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
        entity_id=wbe.entity_id,
        branch=branch_name,
    )

    deleted_wbe = WBE(
        entity_id=wbe.entity_id,
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
