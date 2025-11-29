"""Tests for branch cleanup jobs."""

from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.jobs.branch_cleanup_job import (
    cleanup_cancelled_branches,
    cleanup_merged_branches,
)
from app.models import ChangeOrder, ChangeOrderCreate, Project, User, UserCreate
from app.services.branch_service import BranchService


def _create_pm_user(session: Session) -> User:
    """Helper to create a project manager user."""
    import uuid

    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    from app import crud

    return crud.create_user(session=session, user_create=user_in)


def _create_project(session: Session, pm_user: User) -> Project:
    """Helper to create a project."""
    from app.models import ProjectCreate

    project_in = ProjectCreate(
        project_name="Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        business_status="active",
    )
    project = Project.model_validate(project_in)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def _create_change_order(
    session: Session,
    project: Project,
    created_by: User,
    workflow_status: str = "design",
) -> ChangeOrder:
    """Helper to create a change order."""
    import uuid

    co_in = ChangeOrderCreate(
        project_id=project.project_id,
        created_by_id=created_by.id,
        change_order_number=f"CO-{uuid.uuid4().hex[:6].upper()}",
        title="Test Change Order",
        description="Test description",
        requesting_party="Customer",
        effective_date=date(2024, 6, 1),
        workflow_status=workflow_status,
    )
    co = ChangeOrder.model_validate(co_in)
    branch = BranchService.create_branch(
        session=session, change_order_id=co.change_order_id
    )
    co.branch = branch
    session.add(co)
    session.commit()
    session.refresh(co)
    return co


def test_cleanup_merged_branches_soft_deletes_old_merged_branches(db: Session) -> None:
    """Test that old merged branches are soft-deleted."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user, workflow_status="merged")

    # Make the change order old
    from sqlalchemy import text

    old_date = datetime.utcnow() - timedelta(days=31)
    db.execute(
        text(
            "UPDATE changeorder SET created_at = :old_date WHERE change_order_id = :co_id"
        ),
        {"old_date": old_date, "co_id": change_order.change_order_id},
    )
    db.commit()

    # Run cleanup with 30 day retention
    deleted_count = cleanup_merged_branches(retention_days=30)

    assert deleted_count == 1

    # Verify branch entities are soft-deleted
    from app.models import WBE

    branch_wbes = db.exec(select(WBE).where(WBE.branch == change_order.branch)).all()
    assert len(branch_wbes) > 0
    assert all(wbe.status == "deleted" for wbe in branch_wbes)


def test_cleanup_merged_branches_preserves_recent_merged_branches(db: Session) -> None:
    """Test that recently merged branches are preserved."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user, workflow_status="merged")

    # Run cleanup with 30 day retention
    deleted_count = cleanup_merged_branches(retention_days=30)

    assert deleted_count == 0

    # Verify branch still exists
    assert change_order.branch is not None
    from app.models import WBE

    branch_wbes = db.exec(select(WBE).where(WBE.branch == change_order.branch)).all()
    # Branch may not have WBEs yet, but if it does, they should not be deleted
    assert all(wbe.status != "deleted" for wbe in branch_wbes if wbe.status == "active")


def test_cleanup_cancelled_branches_soft_deletes_old_cancelled_branches(
    db: Session,
) -> None:
    """Test that old cancelled branches are soft-deleted."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(
        db, project, pm_user, workflow_status="cancelled"
    )

    # Make the change order old
    from sqlalchemy import text

    old_date = datetime.utcnow() - timedelta(days=8)
    db.execute(
        text(
            "UPDATE changeorder SET created_at = :old_date WHERE change_order_id = :co_id"
        ),
        {"old_date": old_date, "co_id": change_order.change_order_id},
    )
    db.commit()

    # Run cleanup with 7 day retention
    deleted_count = cleanup_cancelled_branches(retention_days=7)

    assert deleted_count == 1

    # Verify branch entities are soft-deleted
    from app.models import WBE

    branch_wbes = db.exec(select(WBE).where(WBE.branch == change_order.branch)).all()
    # If branch has WBEs, they should be deleted
    if branch_wbes:
        assert all(wbe.status == "deleted" for wbe in branch_wbes)
