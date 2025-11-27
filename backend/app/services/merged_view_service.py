"""Merged view service for displaying main + branch entities with change status."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import WBE, CostElement
from app.services.branch_filtering import apply_branch_filters


class MergedViewService:
    """Service for generating merged views of main and branch entities."""

    @staticmethod
    def get_merged_wbes(
        session: Session,
        project_id: UUID,
        branch: str,
        base_branch: str = "main",
    ) -> list[dict[str, Any]]:
        """
        Get merged view of WBEs from main and branch.

        Returns list of dicts with:
        - entity: WBE instance (latest active version per branch)
        - change_status: 'created' | 'updated' | 'deleted' | 'unchanged'

        Args:
            session: Database session
            project_id: Project ID
            branch: Branch name to merge with main
            base_branch: Base branch to compare against (default: 'main')

        Returns:
            List of merged WBE entities with change status
        """
        # Get all active WBEs from main branch (latest active version per entity)
        # Use subquery to get max version per entity_id, then join to get full records
        main_subquery = (
            select(WBE.entity_id, func.max(WBE.version).label("max_version"))
            .where(WBE.project_id == project_id)
            .where(WBE.branch == base_branch)
            .where(WBE.status == "active")
            .group_by(WBE.entity_id)
        ).subquery()

        main_query = (
            select(WBE)
            .join(
                main_subquery,
                (WBE.entity_id == main_subquery.c.entity_id)
                & (WBE.version == main_subquery.c.max_version),
            )
            .where(WBE.branch == base_branch)
            .where(WBE.status == "active")
        )
        main_wbes = session.exec(main_query).all()

        # Get all active WBEs from branch (latest active version per entity)
        branch_subquery = (
            select(WBE.entity_id, func.max(WBE.version).label("max_version"))
            .where(WBE.project_id == project_id)
            .where(WBE.branch == branch)
            .where(WBE.status == "active")
            .group_by(WBE.entity_id)
        ).subquery()

        branch_query = (
            select(WBE)
            .join(
                branch_subquery,
                (WBE.entity_id == branch_subquery.c.entity_id)
                & (WBE.version == branch_subquery.c.max_version),
            )
            .where(WBE.branch == branch)
            .where(WBE.status == "active")
        )
        branch_wbes = session.exec(branch_query).all()

        # Get deleted WBEs in branch (for entities that exist in main)
        branch_deleted_wbes = session.exec(
            select(WBE)
            .where(WBE.project_id == project_id)
            .where(WBE.branch == branch)
            .where(WBE.status == "deleted")
        ).all()

        # Create maps for quick lookup
        main_wbe_map = {wbe.entity_id: wbe for wbe in main_wbes}
        branch_wbe_map = {wbe.entity_id: wbe for wbe in branch_wbes}
        branch_deleted_map = {wbe.entity_id: wbe for wbe in branch_deleted_wbes}

        merged: list[dict[str, Any]] = []

        # Process main branch entities
        for main_wbe in main_wbes:
            entity_id = main_wbe.entity_id
            branch_wbe = branch_wbe_map.get(entity_id)
            branch_deleted = branch_deleted_map.get(entity_id)

            if branch_deleted:
                # Deleted in branch
                merged.append(
                    {
                        "entity": main_wbe,  # Use main version for display
                        "change_status": "deleted",
                    }
                )
            elif branch_wbe:
                # Exists in both - check if updated
                if _is_wbe_updated(main_wbe, branch_wbe):
                    merged.append(
                        {
                            "entity": branch_wbe,  # Use branch version (takes precedence)
                            "change_status": "updated",
                        }
                    )
                else:
                    merged.append(
                        {
                            "entity": branch_wbe,  # Use branch version even if unchanged
                            "change_status": "unchanged",
                        }
                    )
            else:
                # Only in main - unchanged
                merged.append(
                    {
                        "entity": main_wbe,
                        "change_status": "unchanged",
                    }
                )

        # Process branch-only entities (created)
        for branch_wbe in branch_wbes:
            entity_id = branch_wbe.entity_id
            if entity_id not in main_wbe_map:
                merged.append(
                    {
                        "entity": branch_wbe,
                        "change_status": "created",
                    }
                )

        return merged

    @staticmethod
    def get_merged_cost_elements(
        session: Session,
        project_id: UUID,
        branch: str,
        base_branch: str = "main",
    ) -> list[dict[str, Any]]:
        """
        Get merged view of Cost Elements from main and branch.

        Returns list of dicts with:
        - entity: CostElement instance (latest active version per branch)
        - change_status: 'created' | 'updated' | 'deleted' | 'unchanged'

        Args:
            session: Database session
            project_id: Project ID
            branch: Branch name to merge with main
            base_branch: Base branch to compare against (default: 'main')

        Returns:
            List of merged Cost Element entities with change status
        """
        # Get all active Cost Elements from main branch (latest active version per entity)
        # Need to join with WBE to filter by project_id
        from app.models import WBE as WBEModel

        main_wbe_entity_ids = {
            wbe.entity_id
            for wbe in session.exec(
                apply_branch_filters(
                    select(WBEModel).where(WBEModel.project_id == project_id),
                    WBEModel,
                    branch=base_branch,
                    include_deleted=False,
                )
            ).all()
        }

        # Use subquery to get max version per entity_id for main branch
        main_ce_subquery = (
            select(
                CostElement.entity_id,
                func.max(CostElement.version).label("max_version"),
            )
            .join(WBEModel, CostElement.wbe_id == WBEModel.wbe_id)
            .where(WBEModel.entity_id.in_(list(main_wbe_entity_ids)))  # type: ignore[attr-defined]
            .where(WBEModel.project_id == project_id)
            .where(WBEModel.branch == base_branch)
            .where(CostElement.branch == base_branch)
            .where(CostElement.status == "active")
            .group_by(CostElement.entity_id)
        ).subquery()

        main_cost_elements_query = (
            select(CostElement)
            .join(WBEModel, CostElement.wbe_id == WBEModel.wbe_id)
            .join(
                main_ce_subquery,
                (CostElement.entity_id == main_ce_subquery.c.entity_id)
                & (CostElement.version == main_ce_subquery.c.max_version),
            )
            .where(WBEModel.project_id == project_id)
            .where(WBEModel.branch == base_branch)
            .where(CostElement.branch == base_branch)
            .where(CostElement.status == "active")
        )
        main_cost_elements = session.exec(main_cost_elements_query).all()

        # Get all active Cost Elements from branch (latest active version per entity)
        branch_wbe_entity_ids = {
            wbe.entity_id
            for wbe in session.exec(
                apply_branch_filters(
                    select(WBEModel).where(WBEModel.project_id == project_id),
                    WBEModel,
                    branch=branch,
                    include_deleted=False,
                )
            ).all()
        }

        # Use subquery to get max version per entity_id for branch
        branch_ce_subquery = (
            select(
                CostElement.entity_id,
                func.max(CostElement.version).label("max_version"),
            )
            .join(WBEModel, CostElement.wbe_id == WBEModel.wbe_id)
            .where(WBEModel.entity_id.in_(list(branch_wbe_entity_ids)))  # type: ignore[attr-defined]
            .where(WBEModel.project_id == project_id)
            .where(WBEModel.branch == branch)
            .where(CostElement.branch == branch)
            .where(CostElement.status == "active")
            .group_by(CostElement.entity_id)
        ).subquery()

        branch_cost_elements_query = (
            select(CostElement)
            .join(WBEModel, CostElement.wbe_id == WBEModel.wbe_id)
            .join(
                branch_ce_subquery,
                (CostElement.entity_id == branch_ce_subquery.c.entity_id)
                & (CostElement.version == branch_ce_subquery.c.max_version),
            )
            .where(WBEModel.project_id == project_id)
            .where(WBEModel.branch == branch)
            .where(CostElement.branch == branch)
            .where(CostElement.status == "active")
        )
        branch_cost_elements = session.exec(branch_cost_elements_query).all()

        # Get deleted Cost Elements in branch
        branch_deleted_cost_elements = session.exec(
            select(CostElement)
            .join(WBEModel, CostElement.wbe_id == WBEModel.wbe_id)
            .where(WBEModel.project_id == project_id)
            .where(CostElement.branch == branch)
            .where(CostElement.status == "deleted")
        ).all()

        # Create maps
        main_ce_map = {ce.entity_id: ce for ce in main_cost_elements}
        branch_ce_map = {ce.entity_id: ce for ce in branch_cost_elements}
        branch_deleted_map = {ce.entity_id: ce for ce in branch_deleted_cost_elements}

        merged: list[dict[str, Any]] = []

        # Process main branch entities
        for main_ce in main_cost_elements:
            entity_id = main_ce.entity_id
            branch_ce = branch_ce_map.get(entity_id)
            branch_deleted = branch_deleted_map.get(entity_id)

            if branch_deleted:
                merged.append(
                    {
                        "entity": main_ce,
                        "change_status": "deleted",
                    }
                )
            elif branch_ce:
                if _is_cost_element_updated(main_ce, branch_ce):
                    merged.append(
                        {
                            "entity": branch_ce,
                            "change_status": "updated",
                        }
                    )
                else:
                    merged.append(
                        {
                            "entity": branch_ce,
                            "change_status": "unchanged",
                        }
                    )
            else:
                merged.append(
                    {
                        "entity": main_ce,
                        "change_status": "unchanged",
                    }
                )

        # Process branch-only entities (created)
        for branch_ce in branch_cost_elements:
            entity_id = branch_ce.entity_id
            if entity_id not in main_ce_map:
                merged.append(
                    {
                        "entity": branch_ce,
                        "change_status": "created",
                    }
                )

        return merged


def _is_wbe_updated(main_wbe: WBE, branch_wbe: WBE) -> bool:
    """Check if WBE was updated in branch compared to main."""
    return (
        branch_wbe.machine_type != main_wbe.machine_type
        or branch_wbe.revenue_allocation != main_wbe.revenue_allocation
        or branch_wbe.serial_number != main_wbe.serial_number
        or branch_wbe.contracted_delivery_date != main_wbe.contracted_delivery_date
        or branch_wbe.business_status != main_wbe.business_status
        or branch_wbe.notes != main_wbe.notes
    )


def _is_cost_element_updated(main_ce: CostElement, branch_ce: CostElement) -> bool:
    """Check if Cost Element was updated in branch compared to main."""
    return (
        branch_ce.budget_bac != main_ce.budget_bac
        or branch_ce.revenue_plan != main_ce.revenue_plan
        or branch_ce.department_code != main_ce.department_code
        or branch_ce.department_name != main_ce.department_name
        or branch_ce.business_status != main_ce.business_status
    )
