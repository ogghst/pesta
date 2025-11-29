"""Tests for cleanup jobs."""

from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.jobs.cleanup_jobs import (
    cleanup_merged_change_orders,
    cleanup_old_notifications,
)
from app.models import BranchNotification, ChangeOrder, Project, User, UserCreate


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
    from datetime import date

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


def test_cleanup_old_notifications_removes_old_entries(db: Session) -> None:
    """Test that old notifications are cleaned up."""
    import uuid

    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Create an old notification
    old_date = datetime.utcnow() - timedelta(days=31)
    notification = BranchNotification(
        notification_id=uuid.uuid4(),
        project_id=project.project_id,
        branch="co-001",
        event_type="merge_completed",
        message="Test notification",
        recipients=[pm_user.email],
        context={},
        created_at=old_date,
    )
    db.add(notification)
    db.commit()

    # Run cleanup with 30 day retention
    deleted_count = cleanup_old_notifications(retention_days=30)

    assert deleted_count == 1

    # Verify notification is gone
    remaining = db.exec(select(BranchNotification)).all()
    assert len(remaining) == 0


def test_cleanup_old_notifications_preserves_recent_entries(db: Session) -> None:
    """Test that recent notifications are preserved."""

    from app.services.branch_notifications import BranchNotificationsService

    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Create a recent notification
    _notification = BranchNotificationsService.create_notification(
        session=db,
        project_id=project.project_id,
        branch="co-001",
        event_type="merge_completed",
        message="Test notification",
        recipients=[pm_user.email],
    )
    db.commit()

    # Run cleanup with 30 day retention
    deleted_count = cleanup_old_notifications(retention_days=30)

    assert deleted_count == 0

    # Verify notification still exists
    remaining = db.exec(select(BranchNotification)).all()
    assert len(remaining) == 1


def test_cleanup_merged_change_orders_soft_deletes_old_ones(db: Session) -> None:
    """Test that old merged change orders are soft-deleted."""
    from datetime import date

    from app.models import ChangeOrderCreate

    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Create a merged change order
    co_in = ChangeOrderCreate(
        project_id=project.project_id,
        created_by_id=pm_user.id,
        change_order_number="CO-001",
        title="Test CO",
        description="Test",
        requesting_party="Customer",
        effective_date=date(2024, 6, 1),
        workflow_status="merged",
    )
    change_order = ChangeOrder.model_validate(co_in)
    db.add(change_order)
    db.commit()
    db.refresh(change_order)

    # Manually set created_at to be old
    from sqlalchemy import text

    old_date = datetime.utcnow() - timedelta(days=91)
    db.execute(
        text(
            "UPDATE changeorder SET created_at = :old_date WHERE change_order_id = :co_id"
        ),
        {"old_date": old_date, "co_id": change_order.change_order_id},
    )
    db.commit()

    # Run cleanup with 90 day retention
    deleted_count = cleanup_merged_change_orders(retention_days=90)

    assert deleted_count == 1

    # Verify change order is soft-deleted
    deleted_co = db.exec(
        select(ChangeOrder).where(
            ChangeOrder.change_order_id == change_order.change_order_id
        )
    ).first()
    assert deleted_co is not None
    assert deleted_co.status == "deleted"
