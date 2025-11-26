"""Branch service for managing change order branches.

This service handles branch creation, merging, and deletion for change orders.
Branches enable isolated modifications to WBE and CostElement entities that
can be merged into the main branch upon approval.
"""

import uuid

from sqlmodel import Session, select

from app.models import WBE, BranchLock, ChangeOrder, CostElement
from app.services.branch_notifications import BranchNotificationsService
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

        BranchService._record_branch_notification(
            session=session,
            branch=branch,
            change_order_id=change_order_id,
            event_type="merge_completed",
            message=f"Branch '{branch}' merged into main",
        )

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

    @staticmethod
    def clone_branch(
        session: Session, source_branch: str, target_branch: str | None = None
    ) -> str:
        """Clone all WBE and CostElement versions from one branch into a new branch.

        Args:
            session: Database session.
            source_branch: Name of the branch to clone from.
            target_branch: Optional explicit name for the new branch.

        Returns:
            Name of the newly created branch.
        """

        if source_branch == BranchService.MAIN_BRANCH:
            raise ValueError("Cannot clone the main branch.")

        new_branch = target_branch or f"{source_branch}-clone-{uuid.uuid4().hex[:4]}"
        if new_branch == source_branch:
            raise ValueError("Cloned branch name must differ from source branch.")

        existing = session.exec(select(WBE).where(WBE.branch == new_branch)).first()
        if existing:
            raise ValueError(f"Branch '{new_branch}' already exists.")

        source_wbes = session.exec(select(WBE).where(WBE.branch == source_branch)).all()
        source_cost_elements = session.exec(
            select(CostElement).where(CostElement.branch == source_branch)
        ).all()

        wbe_id_map: dict[uuid.UUID, uuid.UUID] = {}

        for wbe in source_wbes:
            cloned_wbe = WBE(
                entity_id=wbe.entity_id,
                project_id=wbe.project_id,
                machine_type=wbe.machine_type,
                serial_number=wbe.serial_number,
                contracted_delivery_date=wbe.contracted_delivery_date,
                revenue_allocation=wbe.revenue_allocation,
                business_status=wbe.business_status,
                notes=wbe.notes,
                branch=new_branch,
                version=wbe.version,
                status=wbe.status,
            )
            session.add(cloned_wbe)
            session.flush()
            wbe_id_map[wbe.wbe_id] = cloned_wbe.wbe_id

        for cost_element in source_cost_elements:
            cloned_wbe_id = wbe_id_map.get(cost_element.wbe_id)
            if cloned_wbe_id is None:
                continue

            cloned_ce = CostElement(
                entity_id=cost_element.entity_id,
                wbe_id=cloned_wbe_id,
                cost_element_type_id=cost_element.cost_element_type_id,
                department_code=cost_element.department_code,
                department_name=cost_element.department_name,
                budget_bac=cost_element.budget_bac,
                revenue_plan=cost_element.revenue_plan,
                business_status=cost_element.business_status,
                notes=cost_element.notes,
                branch=new_branch,
                version=cost_element.version,
                status=cost_element.status,
            )
            session.add(cloned_ce)

        return new_branch

    @staticmethod
    def get_branch_lock(
        session: Session, project_id: uuid.UUID, branch: str
    ) -> BranchLock | None:
        """Return the lock information for a branch if it exists."""
        return session.exec(
            select(BranchLock)
            .where(BranchLock.project_id == project_id)
            .where(BranchLock.branch == branch)
        ).first()

    @staticmethod
    def lock_branch(
        session: Session,
        project_id: uuid.UUID,
        branch: str,
        locked_by_id: uuid.UUID,
        reason: str | None = None,
    ) -> BranchLock:
        """Create a lock entry for a branch."""
        if branch == BranchService.MAIN_BRANCH:
            raise ValueError("Cannot lock the main branch.")

        existing = BranchService.get_branch_lock(session, project_id, branch)
        if existing:
            raise ValueError("Branch is already locked.")

        lock = BranchLock(
            project_id=project_id,
            branch=branch,
            locked_by_id=locked_by_id,
            reason=reason,
        )
        session.add(lock)
        session.flush()
        return lock

    @staticmethod
    def unlock_branch(session: Session, project_id: uuid.UUID, branch: str) -> None:
        """Release a branch lock if one exists."""
        lock = BranchService.get_branch_lock(session, project_id, branch)
        if lock:
            session.delete(lock)
            session.flush()

    @staticmethod
    def _record_branch_notification(
        session: Session,
        branch: str,
        event_type: str,
        message: str,
        change_order_id: uuid.UUID | None = None,
    ) -> None:
        """Record a notification for a branch event if context is available."""
        change_order: ChangeOrder | None = None
        if change_order_id:
            change_order = session.get(ChangeOrder, change_order_id)
        if not change_order:
            change_order = session.exec(
                select(ChangeOrder).where(ChangeOrder.branch == branch)
            ).first()
        if not change_order:
            return

        recipients = BranchService._collect_change_order_recipients(change_order)
        BranchNotificationsService.create_notification(
            session=session,
            project_id=change_order.project_id,
            branch=branch,
            event_type=event_type,
            message=message,
            recipients=recipients,
            context={
                "change_order_id": str(change_order.change_order_id),
                "project_id": str(change_order.project_id),
            },
        )

    @staticmethod
    def _collect_change_order_recipients(change_order: ChangeOrder | None) -> list[str]:
        """Derive recipient email addresses from a change order's stakeholders."""
        if not change_order:
            return []

        recipients: list[str] = []
        for user in (
            change_order.created_by,
            change_order.approved_by,
            change_order.implemented_by,
        ):
            if user and user.email and str(user.email) not in recipients:
                recipients.append(str(user.email))
        return recipients
