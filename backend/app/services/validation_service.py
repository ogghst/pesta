"""Validation service with merge logic for branch operations.

This module provides validation functions that use merge logic when operating
on branches, ensuring validations consider the merged state (main + branch changes).
"""

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session

from app.models import WBE, CostElement, Project
from app.services.merged_view_service import MergedViewService


def validate_revenue_allocation_with_merge_logic(
    session: Session,
    project_id: UUID,
    new_revenue_allocation: Decimal,
    branch: str,
    exclude_entity_id: UUID | None = None,
) -> None:
    """Validate WBE revenue allocation against project limit using merge logic.

    When branch != 'main', this function simulates the merged state (main + branch)
    to ensure validation will pass after merge.

    Args:
        session: Database session
        project_id: Project ID
        new_revenue_allocation: New revenue allocation value being set
        branch: Branch name ('main' or branch name)
        exclude_entity_id: Entity ID to exclude from sum (for updates)

    Raises:
        HTTPException: If validation fails
    """
    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    if branch == "main":
        # Direct validation for main branch
        from sqlmodel import select

        statement = select(WBE).where(WBE.project_id == project_id)
        statement = statement.where(WBE.branch == "main")
        statement = statement.where(WBE.status == "active")

        if exclude_entity_id:
            statement = statement.where(WBE.entity_id != exclude_entity_id)

        wbes = session.exec(statement).all()
        total_revenue_allocation = sum(wbe.revenue_allocation for wbe in wbes)
    else:
        # Use merge logic for branch operations
        merged_wbes = MergedViewService.get_merged_wbes(
            session=session, project_id=project_id, branch=branch
        )

        # Sum revenue from merged view (exclude deleted, use branch version if updated)
        total_revenue_allocation = Decimal("0.00")
        for item in merged_wbes:
            if item["change_status"] == "deleted":
                continue  # Skip deleted entities

            wbe = item["entity"]
            if exclude_entity_id and wbe.entity_id == exclude_entity_id:
                continue  # Exclude the entity being updated

            total_revenue_allocation += wbe.revenue_allocation

    # Add new revenue allocation
    new_total = total_revenue_allocation + new_revenue_allocation

    # Compare against project contract value
    if new_total > project.contract_value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Total revenue allocation for WBEs (€{new_total:,.2f}) "
                f"exceeds project contract value (€{project.contract_value:,.2f})"
            ),
        )


def validate_revenue_plan_with_merge_logic(
    session: Session,
    wbe_id: UUID,
    new_revenue_plan: Decimal,
    branch: str,
    exclude_entity_id: UUID | None = None,
) -> None:
    """Validate CostElement revenue plan against WBE limit using merge logic.

    When branch != 'main', this function simulates the merged state (main + branch)
    to ensure validation will pass after merge.

    Args:
        session: Database session
        wbe_id: WBE ID (primary key) - used to find WBE entity_id
        new_revenue_plan: New revenue plan value being set
        branch: Branch name ('main' or branch name)
        exclude_entity_id: Entity ID to exclude from sum (for updates)

    Raises:
        HTTPException: If validation fails
    """
    # Get WBE to find its entity_id and project_id
    wbe = session.get(WBE, wbe_id)
    if not wbe:
        raise HTTPException(status_code=400, detail="WBE not found")

    wbe_entity_id = wbe.entity_id
    project_id = wbe.project_id

    if branch == "main":
        # Direct validation for main branch
        from sqlmodel import select

        statement = select(CostElement).where(CostElement.wbe_id == wbe_id)
        statement = statement.where(CostElement.branch == "main")
        statement = statement.where(CostElement.status == "active")

        if exclude_entity_id:
            statement = statement.where(CostElement.entity_id != exclude_entity_id)

        cost_elements = session.exec(statement).all()
        total_revenue_plan = sum(ce.revenue_plan for ce in cost_elements)
    else:
        # Use merge logic for branch operations
        # Get merged cost elements for the project
        merged_cost_elements = MergedViewService.get_merged_cost_elements(
            session=session, project_id=project_id, branch=branch
        )

        # Filter to cost elements for this WBE and sum revenue
        total_revenue_plan = Decimal("0.00")
        for item in merged_cost_elements:
            if item["change_status"] == "deleted":
                continue  # Skip deleted entities

            ce = item["entity"]
            # Check if this cost element belongs to the WBE (by entity_id)
            # We need to check if the cost element's WBE has the same entity_id
            ce_wbe = session.get(WBE, ce.wbe_id)
            if ce_wbe and ce_wbe.entity_id == wbe_entity_id:
                if exclude_entity_id and ce.entity_id == exclude_entity_id:
                    continue  # Exclude the entity being updated

                total_revenue_plan += ce.revenue_plan

        # Also need to get WBE revenue allocation (may be from branch)
        # Get merged WBEs to find the WBE's revenue allocation in merged state
        merged_wbes = MergedViewService.get_merged_wbes(
            session=session, project_id=project_id, branch=branch
        )
        wbe_revenue_allocation = None
        for item in merged_wbes:
            if item["change_status"] == "deleted":
                continue
            wbe_item = item["entity"]
            if wbe_item.entity_id == wbe_entity_id:
                wbe_revenue_allocation = wbe_item.revenue_allocation
                break

        if wbe_revenue_allocation is None:
            raise HTTPException(status_code=400, detail="WBE not found in merged view")

        # Add new revenue plan
        new_total = total_revenue_plan + new_revenue_plan

        # Compare against WBE revenue allocation from merged view
        if new_total > wbe_revenue_allocation:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Total revenue plan for cost elements (€{new_total:,.2f}) "
                    f"exceeds WBE revenue allocation (€{wbe_revenue_allocation:,.2f})"
                ),
            )
        return  # Early return for branch operations

    # For main branch, use direct WBE revenue allocation
    total_revenue_plan += new_revenue_plan

    # Compare against wbe.revenue_allocation
    if total_revenue_plan > wbe.revenue_allocation:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Total revenue plan for cost elements (€{total_revenue_plan:,.2f}) "
                f"exceeds WBE revenue allocation (€{wbe.revenue_allocation:,.2f})"
            ),
        )
