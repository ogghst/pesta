"""Branch service for managing change order branches.

This service handles branch creation, merging, and deletion for change orders.
Branches enable isolated modifications to WBE and CostElement entities that
can be merged into the main branch upon approval.
"""

import uuid

from sqlmodel import Session, select

from app.models import WBE, ChangeOrder, CostElement
from app.services.version_service import VersionService


class BranchService:
    """Service for managing change order branches."""

    MAIN_BRANCH = "main"

    @staticmethod
    def _generate_short_id(change_order_id: uuid.UUID) -> str:
        """Generate a short identifier from change order ID."""
        uuid_hex = str(change_order_id).replace("-", "")
        return uuid_hex[:6]

    @staticmethod
    def create_branch(session: Session, change_order_id: uuid.UUID) -> str:
        """Create a new branch for a change order."""
        change_order = session.get(ChangeOrder, change_order_id)
        if not change_order:
            raise ValueError(f"Change order {change_order_id} not found")

        short_id = BranchService._generate_short_id(change_order_id)
        return f"co-{short_id}"

    @staticmethod
    def get_branch_for_change_order(
        session: Session, change_order_id: uuid.UUID
    ) -> str | None:
        """Get the branch name for a change order."""
        change_order = session.get(ChangeOrder, change_order_id)
        if not change_order:
            return None

        short_id = BranchService._generate_short_id(change_order_id)
        return f"co-{short_id}"

    @staticmethod
    def list_branches_for_project(session: Session, project_id: uuid.UUID) -> list[str]:
        """List all branches for a project (derived from change orders)."""
        change_orders = session.exec(
            select(ChangeOrder).where(ChangeOrder.project_id == project_id)
        ).all()

        branches = []
        for co in change_orders:
            branch_name = BranchService.get_branch_for_change_order(
                session, co.change_order_id
            )
            if branch_name:
                branches.append(branch_name)

        return branches

    @staticmethod
    def _create_wbe_version(
        session: Session,
        source: WBE,
        target_branch: str,
        status: str | None = None,
    ) -> WBE:
        """Create a new WBE version in the target branch based on source data."""
        next_version = VersionService.get_next_version(
            session=session,
            entity_type="wbe",
            entity_id=source.entity_id,
            branch=target_branch,
        )
        new_wbe = WBE(
            entity_id=source.entity_id,
            project_id=source.project_id,
            machine_type=source.machine_type,
            serial_number=source.serial_number,
            contracted_delivery_date=source.contracted_delivery_date,
            revenue_allocation=source.revenue_allocation,
            business_status=source.business_status,
            notes=source.notes,
            branch=target_branch,
            version=next_version,
            status=status or source.status,
        )
        session.add(new_wbe)
        session.flush()
        return new_wbe

    @staticmethod
    def _create_cost_element_version(
        session: Session,
        source: CostElement,
        target_wbe_id: uuid.UUID,
        target_branch: str,
        status: str | None = None,
    ) -> CostElement:
        """Create a new CostElement version in the target branch."""
        next_version = VersionService.get_next_version(
            session=session,
            entity_type="costelement",
            entity_id=source.entity_id,
            branch=target_branch,
        )
        new_cost_element = CostElement(
            entity_id=source.entity_id,
            wbe_id=target_wbe_id,
            cost_element_type_id=source.cost_element_type_id,
            department_code=source.department_code,
            department_name=source.department_name,
            budget_bac=source.budget_bac,
            revenue_plan=source.revenue_plan,
            business_status=source.business_status,
            notes=source.notes,
            branch=target_branch,
            version=next_version,
            status=status or source.status,
        )
        session.add(new_cost_element)
        session.flush()
        return new_cost_element

    @staticmethod
    def merge_branch(
        session: Session,
        branch: str,
        change_order_id: uuid.UUID | None = None,
    ) -> None:
        """Merge a change-order branch into the main branch."""
        if branch == BranchService.MAIN_BRANCH:
            raise ValueError("Cannot merge the main branch into itself.")

        if change_order_id:
            expected_branch = BranchService.get_branch_for_change_order(
                session, change_order_id
            )
            if expected_branch and expected_branch != branch:
                raise ValueError(
                    f"Branch '{branch}' does not match change order {change_order_id}"
                )

        target_branch = BranchService.MAIN_BRANCH
        wbe_id_map: dict[uuid.UUID, uuid.UUID] = {}

        branch_wbes = session.exec(select(WBE).where(WBE.branch == branch)).all()

        for wbe in branch_wbes:
            if wbe.status not in {"active", "deleted"}:
                continue
            new_wbe = BranchService._create_wbe_version(
                session=session,
                source=wbe,
                target_branch=target_branch,
                status=wbe.status,
            )
            wbe_id_map[wbe.entity_id] = new_wbe.wbe_id
            wbe.status = "merged"
            session.add(wbe)

        branch_cost_elements = session.exec(
            select(CostElement).where(CostElement.branch == branch)
        ).all()

        for cost_element in branch_cost_elements:
            if cost_element.status not in {"active", "deleted"}:
                continue

            source_wbe = session.get(WBE, cost_element.wbe_id)
            if not source_wbe:
                continue

            target_wbe_id = wbe_id_map.get(source_wbe.entity_id)
            if target_wbe_id is None:
                # Fallback to latest main-branch WBE or create one if missing
                target_wbe = session.exec(
                    select(WBE)
                    .where(WBE.entity_id == source_wbe.entity_id)
                    .where(WBE.branch == target_branch)
                    .order_by(WBE.version.desc())
                ).first()
                if not target_wbe:
                    target_wbe = BranchService._create_wbe_version(
                        session=session,
                        source=source_wbe,
                        target_branch=target_branch,
                        status=source_wbe.status,
                    )
                target_wbe_id = target_wbe.wbe_id
                wbe_id_map[source_wbe.entity_id] = target_wbe_id

            BranchService._create_cost_element_version(
                session=session,
                source=cost_element,
                target_wbe_id=target_wbe_id,
                target_branch=target_branch,
                status=cost_element.status,
            )
            cost_element.status = "merged"
            session.add(cost_element)

    @staticmethod
    def delete_branch(session: Session, branch: str) -> None:
        """Soft delete a branch by setting status='deleted' for all branch entities.

        This performs a soft delete, preserving all versions of WBE and CostElement
        entities in the branch. The entities will not appear in normal queries
        (which filter by status='active'), but can be queried with include_deleted=True.

        Args:
            session: Database session
            branch: Branch name to delete (e.g., 'co-001')

        Raises:
            ValueError: If attempting to delete the main branch
        """
        if branch == BranchService.MAIN_BRANCH:
            raise ValueError("Cannot delete the main branch.")

        # Get all WBEs in the branch (all versions, all statuses)
        branch_wbes = session.exec(select(WBE).where(WBE.branch == branch)).all()
        for wbe in branch_wbes:
            wbe.status = "deleted"
            session.add(wbe)

        # Get all CostElements in the branch (all versions, all statuses)
        branch_cost_elements = session.exec(
            select(CostElement).where(CostElement.branch == branch)
        ).all()
        for cost_element in branch_cost_elements:
            cost_element.status = "deleted"
            session.add(cost_element)
