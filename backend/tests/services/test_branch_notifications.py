"""Tests for branch notifications service."""


from sqlmodel import Session, select

from app.models import BranchNotification
from app.services.branch_notifications import BranchNotificationsService
from app.services.branch_service import BranchService
from tests.services.test_branch_service import (
    _create_change_order,
    _create_pm_user,
    _create_project,
)


def test_create_notification_persists_record(db: Session) -> None:
    """Creating a notification should persist it in the database."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    notification = BranchNotificationsService.create_notification(
        session=db,
        project_id=project.project_id,
        branch=branch,
        event_type="merge_completed",
        message="Branch merged into main",
        recipients=["pm@example.com", "lead@example.com"],
        context={"change_order_id": str(change_order.change_order_id)},
    )
    db.commit()

    stored = db.exec(
        select(BranchNotification).where(
            BranchNotification.notification_id == notification.notification_id
        )
    ).one()

    assert stored.branch == branch
    assert stored.event_type == "merge_completed"
    assert stored.recipients == ["pm@example.com", "lead@example.com"]
    assert stored.context["change_order_id"] == str(change_order.change_order_id)


def test_list_notifications_returns_latest_first(db: Session) -> None:
    """Listing notifications should return most recent entries first."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    BranchNotificationsService.create_notification(
        session=db,
        project_id=project.project_id,
        branch=branch,
        event_type="conflict_detected",
        message="Conflicts detected during merge preview",
        recipients=["pm@example.com"],
        context={"conflicts": 2},
    )
    BranchNotificationsService.create_notification(
        session=db,
        project_id=project.project_id,
        branch=branch,
        event_type="merge_completed",
        message="Merge completed successfully",
        recipients=["pm@example.com"],
        context={"merged_by": str(pm_user.id)},
    )
    db.commit()

    notifications = BranchNotificationsService.list_notifications(
        session=db, project_id=project.project_id, limit=5
    )

    assert len(notifications) == 2
    assert notifications[0].event_type == "merge_completed"
    assert notifications[1].event_type == "conflict_detected"


def test_merge_branch_emits_notification(db: Session) -> None:
    """Branch merge events should automatically record notifications."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )
    change_order.branch = branch
    db.add(change_order)
    db.commit()

    BranchService.merge_branch(
        session=db, branch=branch, change_order_id=change_order.change_order_id
    )

    notifications = db.exec(
        select(BranchNotification).where(BranchNotification.branch == branch)
    ).all()
    assert len(notifications) == 1
    assert notifications[0].event_type == "merge_completed"
    assert notifications[0].recipients == [pm_user.email]
