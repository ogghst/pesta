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
    BudgetAllocation,
    BudgetAllocationCreate,
    CostElement,
    CostElementCreate,
    CostElementPublic,
    CostElementsPublic,
    CostElementType,
    CostElementUpdate,
    Message,
)
from app.services.branch_filtering import (
    apply_branch_filters,
    get_branch_context,
    resolve_entity_by_entity_id,
)
from app.services.entity_versioning import (
    create_entity_with_version,
    ensure_branch_version,
)
from app.services.merged_view_service import MergedViewService
from app.services.validation_service import validate_revenue_plan_with_merge_logic
from app.services.version_service import VersionService

router = APIRouter(prefix="/cost-elements", tags=["cost-elements"])


def _end_of_day(control_date: date) -> datetime:
    """Return timezone-aware datetime representing the end of the control date."""
    return datetime.combine(control_date, time.max, tzinfo=timezone.utc)


def create_budget_allocation_for_cost_element(
    session: Session,
    cost_element: CostElement,
    allocation_type: str,
    created_by_id: uuid.UUID,
) -> BudgetAllocation:
    """
    Create a BudgetAllocation record for a CostElement.

    Args:
        session: Database session
        cost_element: The CostElement to create allocation for
        allocation_type: Type of allocation ("initial" or "update")
        created_by_id: ID of user creating the allocation

    Returns:
        Created BudgetAllocation record
    """
    budget_allocation_in = BudgetAllocationCreate(
        cost_element_id=cost_element.cost_element_id,
        allocation_date=date.today(),
        budget_amount=cost_element.budget_bac,
        revenue_amount=cost_element.revenue_plan,
        allocation_type=allocation_type,
        description=f"{allocation_type.capitalize()} budget allocation",
        created_by_id=created_by_id,
    )
    budget_allocation = BudgetAllocation.model_validate(budget_allocation_in)
    budget_allocation = create_entity_with_version(
        session=session,
        entity=budget_allocation,
        entity_type="budget_allocation",
        entity_id=budget_allocation.budget_allocation_id,
    )
    return budget_allocation


def validate_revenue_plan_against_wbe_limit(
    session: Session,
    wbe_id: uuid.UUID,
    new_revenue_plan: Decimal,
    exclude_cost_element_id: uuid.UUID | None = None,
) -> None:
    """
    Validate that sum of cost element revenue_plan does not exceed WBE revenue_allocation.
    Raises HTTPException(400) if validation fails.

    Args:
        session: Database session
        wbe_id: ID of the WBE to validate against
        new_revenue_plan: The new revenue_plan value being set
        exclude_cost_element_id: Cost element ID to exclude from the sum (for updates)
    """
    # Get WBE and its revenue_allocation
    wbe = session.get(WBE, wbe_id)
    if not wbe:
        raise HTTPException(status_code=400, detail="WBE not found")

    # Query all cost elements for this WBE (excluding the one being updated if specified)
    # Note: This validation should consider only active cost elements in the same branch as the WBE
    statement = select(CostElement).where(CostElement.wbe_id == wbe_id)
    statement = apply_branch_filters(
        statement, CostElement, branch=get_branch_context()
    )
    if exclude_cost_element_id:
        statement = statement.where(
            CostElement.cost_element_id != exclude_cost_element_id
        )

    cost_elements = session.exec(statement).all()

    # Sum existing revenue_plan values
    total_revenue_plan = sum(ce.revenue_plan for ce in cost_elements)

    # Add new_revenue_plan
    new_total = total_revenue_plan + new_revenue_plan

    # Compare against wbe.revenue_allocation
    if new_total > wbe.revenue_allocation:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Total revenue plan for cost elements (€{new_total:,.2f}) "
                f"exceeds WBE revenue allocation (€{wbe.revenue_allocation:,.2f})"
            ),
        )


@router.get("/", response_model=CostElementsPublic)
def read_cost_elements(
    session: SessionDep,
    _current_user: CurrentUser,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
    skip: int = 0,
    limit: int = 100,
    wbe_id: uuid.UUID | None = Query(default=None, description="Filter by WBE ID"),
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
    view_mode: str = Query(
        default="merged", description="View mode: 'merged' (default) or 'branch-only'"
    ),
) -> Any:
    """
    Retrieve cost elements.

    When view_mode='merged' (default), returns merged view of main + branch entities
    with change_status field indicating: 'created', 'updated', 'deleted', or 'unchanged'.

    When view_mode='branch-only', returns only entities from the specified branch
    (existing behavior).
    """
    cutoff = _end_of_day(control_date)

    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Handle merged view mode
    if view_mode == "merged" and wbe_id:
        # Get WBE to find project_id
        wbe = session.get(WBE, wbe_id)
        if not wbe:
            raise HTTPException(status_code=404, detail="WBE not found")

        # Get merged view using MergedViewService
        merged_ces = MergedViewService.get_merged_cost_elements(
            session=session, project_id=wbe.project_id, branch=branch_name
        )

        # Filter by wbe_id and control date, then apply pagination
        filtered_merged = [
            item
            for item in merged_ces
            if item["entity"].wbe_id == wbe_id and item["entity"].created_at <= cutoff
        ]
        total_count = len(filtered_merged)
        paginated = filtered_merged[skip : skip + limit]

        # Convert to CostElementPublic with change_status
        ces_public = []
        for item in paginated:
            ce = item["entity"]
            ce_dict = {
                "entity_id": ce.entity_id,
                "cost_element_id": ce.cost_element_id,
                "wbe_id": ce.wbe_id,
                "cost_element_type_id": ce.cost_element_type_id,
                "department_code": ce.department_code,
                "department_name": ce.department_name,
                "budget_bac": ce.budget_bac,
                "revenue_plan": ce.revenue_plan,
                "business_status": ce.business_status,
                "notes": ce.notes,
                "status": ce.status,
                "version": ce.version,
                "branch": ce.branch,
                "change_status": item["change_status"],
            }
            ces_public.append(CostElementPublic.model_validate(ce_dict))

        return CostElementsPublic(data=ces_public, count=total_count)

    # Branch-only view mode (existing behavior)
    if wbe_id:
        # Filter by WBE
        count_statement = (
            select(func.count())
            .select_from(CostElement)
            .where(CostElement.wbe_id == wbe_id)
            .where(CostElement.created_at <= cutoff)
        )
        count_statement = apply_branch_filters(
            count_statement, CostElement, branch=branch_name
        )
        count = session.exec(count_statement).one()

        statement = (
            select(CostElement)
            .where(CostElement.wbe_id == wbe_id)
            .where(CostElement.created_at <= cutoff)
        )
        statement = apply_branch_filters(statement, CostElement, branch=branch_name)
        statement = statement.order_by(
            CostElement.created_at.asc(), CostElement.cost_element_id.asc()
        )
        statement = statement.offset(skip).limit(limit)
    else:
        # Get all
        count_statement = (
            select(func.count())
            .select_from(CostElement)
            .where(CostElement.created_at <= cutoff)
        )
        count_statement = apply_branch_filters(
            count_statement, CostElement, branch=branch_name
        )
        count = session.exec(count_statement).one()

        statement = select(CostElement).where(CostElement.created_at <= cutoff)
        statement = apply_branch_filters(statement, CostElement, branch=branch_name)
        statement = statement.order_by(
            CostElement.created_at.asc(), CostElement.cost_element_id.asc()
        )
        statement = statement.offset(skip).limit(limit)

    cost_elements = session.exec(statement).all()
    return CostElementsPublic(data=cost_elements, count=count)


@router.get("/by-entity-id", response_model=CostElementPublic)
def read_cost_element_by_entity_id(
    session: SessionDep,
    _current_user: CurrentUser,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
    entity_id: uuid.UUID = Query(..., description="Entity ID of the cost element"),
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
    view_mode: str = Query(
        default="merged", description="View mode: 'merged' (default) or 'branch-only'"
    ),
) -> Any:
    """
    Get cost element by entity_id and branch.

    When view_mode='merged' (default), returns cost element with change_status field
    indicating its status relative to main branch.

    When view_mode='branch-only', returns cost element from specified branch only.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Handle merged view mode
    if view_mode == "merged":
        # Resolve entity to get wbe_id and project_id
        try:
            cost_element = resolve_entity_by_entity_id(
                session, CostElement, entity_id, branch_name
            )
        except ValueError:
            raise HTTPException(status_code=404, detail="Cost element not found")

        if cost_element.created_at > _end_of_day(control_date):
            raise HTTPException(status_code=404, detail="Cost element not found")

        # Get WBE to find project_id
        wbe = session.get(WBE, cost_element.wbe_id)
        if not wbe:
            raise HTTPException(status_code=404, detail="WBE not found")

        # Get merged view for the project
        merged_ces = MergedViewService.get_merged_cost_elements(
            session=session, project_id=wbe.project_id, branch=branch_name
        )

        # Find the cost element in merged view by entity_id
        merged_item = None
        for item in merged_ces:
            if item["entity"].entity_id == entity_id:
                merged_item = item
                break

        if not merged_item:
            raise HTTPException(status_code=404, detail="Cost element not found")

        # Return with change_status
        ce_entity = merged_item["entity"]
        ce_dict = {
            "entity_id": ce_entity.entity_id,
            "cost_element_id": ce_entity.cost_element_id,
            "wbe_id": ce_entity.wbe_id,
            "cost_element_type_id": ce_entity.cost_element_type_id,
            "department_code": ce_entity.department_code,
            "department_name": ce_entity.department_name,
            "budget_bac": ce_entity.budget_bac,
            "revenue_plan": ce_entity.revenue_plan,
            "business_status": ce_entity.business_status,
            "notes": ce_entity.notes,
            "status": ce_entity.status,
            "version": ce_entity.version,
            "branch": ce_entity.branch,
            "change_status": merged_item["change_status"],
        }
        return CostElementPublic.model_validate(ce_dict)

    # Branch-only view mode (existing behavior)
    # Resolve by entity_id and branch
    try:
        cost_element = resolve_entity_by_entity_id(
            session, CostElement, entity_id, branch_name
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Cost element not found")

    if cost_element.created_at > _end_of_day(control_date):
        raise HTTPException(status_code=404, detail="Cost element not found")
    return cost_element


@router.get("/{id}", response_model=CostElementPublic)
def read_cost_element(
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
    Get cost element by primary key (for backward compatibility with URLs).

    This endpoint resolves the primary key to entity_id and then uses entity_id-based logic.
    """
    # Get cost element by primary key to find entity_id
    cost_element = session.get(CostElement, id)
    if not cost_element or cost_element.created_at > _end_of_day(control_date):
        raise HTTPException(status_code=404, detail="Cost element not found")

    # Use entity_id to call the entity_id-based endpoint logic
    branch_name = branch or get_branch_context()

    # Handle merged view mode
    if view_mode == "merged":
        # Resolve entity to get wbe_id and project_id
        try:
            ce_resolved = resolve_entity_by_entity_id(
                session, CostElement, cost_element.entity_id, branch_name
            )
        except ValueError:
            raise HTTPException(status_code=404, detail="Cost element not found")

        if ce_resolved.created_at > _end_of_day(control_date):
            raise HTTPException(status_code=404, detail="Cost element not found")

        # Get WBE to find project_id
        wbe = session.get(WBE, ce_resolved.wbe_id)
        if not wbe:
            raise HTTPException(status_code=404, detail="WBE not found")

        # Get merged view for the project
        merged_ces = MergedViewService.get_merged_cost_elements(
            session=session, project_id=wbe.project_id, branch=branch_name
        )

        # Find the cost element in merged view by entity_id
        merged_item = None
        for item in merged_ces:
            if item["entity"].entity_id == cost_element.entity_id:
                merged_item = item
                break

        if not merged_item:
            raise HTTPException(status_code=404, detail="Cost element not found")

        # Return with change_status
        ce_entity = merged_item["entity"]
        ce_dict = {
            "entity_id": ce_entity.entity_id,
            "cost_element_id": ce_entity.cost_element_id,
            "wbe_id": ce_entity.wbe_id,
            "department_code": ce_entity.department_code,
            "department_name": ce_entity.department_name,
            "budget_bac": ce_entity.budget_bac,
            "revenue_plan": ce_entity.revenue_plan,
            "business_status": ce_entity.business_status,
            "notes": ce_entity.notes,
            "status": ce_entity.status,
            "version": ce_entity.version,
            "branch": ce_entity.branch,
            "change_status": merged_item["change_status"],
        }
        return CostElementPublic.model_validate(ce_dict)

    # Branch-only view mode
    try:
        ce_resolved = resolve_entity_by_entity_id(
            session, CostElement, cost_element.entity_id, branch_name
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Cost element not found")

    if ce_resolved.created_at > _end_of_day(control_date):
        raise HTTPException(status_code=404, detail="Cost element not found")
    return ce_resolved


@router.post("/", response_model=CostElementPublic)
def create_cost_element(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    cost_element_in: CostElementCreate,
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Any:
    """
    Create new cost element.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Validate that WBE exists (in the same branch)
    statement = select(WBE).where(WBE.wbe_id == cost_element_in.wbe_id)
    statement = apply_branch_filters(statement, WBE, branch=branch_name)
    wbe = session.exec(statement).first()
    if not wbe:
        raise HTTPException(status_code=400, detail="WBE not found")

    # Validate that cost element type exists
    cost_element_type = session.get(
        CostElementType, cost_element_in.cost_element_type_id
    )
    if not cost_element_type:
        raise HTTPException(status_code=400, detail="Cost element type not found")

    # Validate revenue_plan does not exceed WBE revenue_allocation
    # Use merge logic validation for branch operations
    validate_revenue_plan_with_merge_logic(
        session=session,
        wbe_id=cost_element_in.wbe_id,
        new_revenue_plan=cost_element_in.revenue_plan,
        branch=branch_name,
    )

    # Create cost element with version, status, and branch
    cost_element = CostElement.model_validate(cost_element_in)
    next_version = VersionService.get_next_version(
        session=session,
        entity_type="costelement",
        entity_id=cost_element.entity_id,
        branch=branch_name,
    )
    cost_element.version = next_version
    cost_element.status = "active"
    cost_element.branch = branch_name
    session.add(cost_element)
    session.flush()  # Flush to get cost_element_id without committing

    # Create initial BudgetAllocation record
    create_budget_allocation_for_cost_element(
        session=session,
        cost_element=cost_element,
        allocation_type="initial",
        created_by_id=_current_user.id,
    )

    session.commit()
    session.refresh(cost_element)
    return cost_element


@router.put("/", response_model=CostElementPublic)
def update_cost_element(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    entity_id: uuid.UUID = Query(..., description="Entity ID of the cost element"),
    cost_element_in: CostElementUpdate,
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Any:
    """
    Update a cost element. Creates a new version in the specified branch.

    If entity only exists in main branch, creates a new version in the specified branch
    with the user's changes. If entity exists in the branch, performs normal version increment.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Ensure entity exists in branch (creates version 1 if only in main)
    if branch_name != "main":
        cost_element = ensure_branch_version(
            session, CostElement, entity_id, branch_name, "costelement"
        )
    else:
        try:
            cost_element = resolve_entity_by_entity_id(
                session, CostElement, entity_id, branch_name
            )
        except ValueError:
            raise HTTPException(status_code=404, detail="Cost element not found")

    update_dict = cost_element_in.model_dump(exclude_unset=True)

    # Validate revenue_plan if it's being updated
    if "revenue_plan" in update_dict:
        new_revenue_plan = update_dict["revenue_plan"]
        validate_revenue_plan_with_merge_logic(
            session=session,
            wbe_id=cost_element.wbe_id,
            new_revenue_plan=new_revenue_plan,
            branch=branch_name,
            exclude_entity_id=entity_id,
        )

    # Check if budget_bac or revenue_plan are being updated
    budget_changed = "budget_bac" in update_dict
    revenue_changed = "revenue_plan" in update_dict

    # Store old values to check if they actually changed
    old_budget_bac = cost_element.budget_bac
    old_revenue_plan = cost_element.revenue_plan

    # Get next version number for this entity in this branch
    next_version = VersionService.get_next_version(
        session=session,
        entity_type="costelement",
        entity_id=entity_id,
        branch=branch_name,
    )

    # Create new version: copy existing cost element and update with new values
    new_cost_element = CostElement(
        entity_id=entity_id,
        wbe_id=cost_element.wbe_id,
        cost_element_type_id=cost_element.cost_element_type_id,
        department_code=update_dict.get(
            "department_code", cost_element.department_code
        ),
        department_name=update_dict.get(
            "department_name", cost_element.department_name
        ),
        budget_bac=update_dict.get("budget_bac", cost_element.budget_bac),
        revenue_plan=update_dict.get("revenue_plan", cost_element.revenue_plan),
        business_status=update_dict.get(
            "business_status", cost_element.business_status
        ),
        notes=update_dict.get("notes", cost_element.notes),
        version=next_version,
        status="active",
        branch=branch_name,
    )

    session.add(new_cost_element)
    session.flush()  # Flush to get updated values without committing

    # Create new BudgetAllocation if budget_bac or revenue_plan changed
    if budget_changed or revenue_changed:
        # Check if values actually changed (to handle cases where same value is set)
        if (budget_changed and new_cost_element.budget_bac != old_budget_bac) or (
            revenue_changed and new_cost_element.revenue_plan != old_revenue_plan
        ):
            create_budget_allocation_for_cost_element(
                session=session,
                cost_element=new_cost_element,
                allocation_type="update",
                created_by_id=_current_user.id,
            )

    session.commit()
    session.refresh(new_cost_element)
    return new_cost_element


@router.delete("/")
def delete_cost_element(
    session: SessionDep,
    _current_user: CurrentUser,
    entity_id: uuid.UUID = Query(..., description="Entity ID of the cost element"),
    branch: str | None = Query(
        default=None, description="Branch name (defaults to 'main')"
    ),
) -> Message:
    """
    Delete a cost element (soft delete: sets status='deleted').

    If entity only exists in main branch, creates a new version in the specified branch
    with status='deleted'. If entity exists in the branch, performs normal soft delete.
    """
    # Use provided branch or default to current context or 'main'
    branch_name = branch or get_branch_context()

    # Ensure entity exists in branch (creates version 1 if only in main)
    if branch_name != "main":
        cost_element = ensure_branch_version(
            session, CostElement, entity_id, branch_name, "costelement"
        )
    else:
        try:
            cost_element = resolve_entity_by_entity_id(
                session, CostElement, entity_id, branch_name
            )
        except ValueError:
            raise HTTPException(status_code=404, detail="Cost element not found")

    # Soft delete: create new version with status='deleted'
    next_version = VersionService.get_next_version(
        session=session,
        entity_type="costelement",
        entity_id=entity_id,
        branch=branch_name,
    )

    deleted_cost_element = CostElement(
        entity_id=entity_id,
        wbe_id=cost_element.wbe_id,
        cost_element_type_id=cost_element.cost_element_type_id,
        department_code=cost_element.department_code,
        department_name=cost_element.department_name,
        budget_bac=cost_element.budget_bac,
        revenue_plan=cost_element.revenue_plan,
        business_status=cost_element.business_status,
        notes=cost_element.notes,
        version=next_version,
        status="deleted",
        branch=branch_name,
    )

    session.add(deleted_cost_element)
    session.commit()
    return Message(message="Cost element deleted successfully")
