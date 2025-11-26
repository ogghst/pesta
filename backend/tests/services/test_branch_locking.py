"""Tests for branch locking."""


import pytest
from sqlmodel import Session, select

from app.models import BranchLock
from app.services.branch_service import BranchService
from tests.services.test_branch_service import (
    _create_change_order,
    _create_pm_user,
    _create_project,
)


def test_lock_branch_creates_lock_entry(db: Session) -> None:
    """Locking a branch should create a unique lock record."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    lock = BranchService.lock_branch(
        session=db,
        project_id=project.project_id,
        branch=branch,
        locked_by_id=pm_user.id,
        reason="Testing lock",
    )

    db.commit()

    stored_lock = db.exec(
        select(BranchLock)
        .where(BranchLock.project_id == project.project_id)
        .where(BranchLock.branch == branch)
    ).first()

    assert stored_lock is not None
    assert stored_lock.lock_id == lock.lock_id
    assert stored_lock.reason == "Testing lock"

    with pytest.raises(ValueError):
        BranchService.lock_branch(
            session=db,
            project_id=project.project_id,
            branch=branch,
            locked_by_id=pm_user.id,
        )


def test_unlock_branch_removes_entry(db: Session) -> None:
    """Unlocking a branch should remove the lock record."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    BranchService.lock_branch(
        session=db,
        project_id=project.project_id,
        branch=branch,
        locked_by_id=pm_user.id,
    )
    db.commit()

    BranchService.unlock_branch(
        session=db, project_id=project.project_id, branch=branch
    )
    db.commit()

    lock = BranchService.get_branch_lock(
        session=db, project_id=project.project_id, branch=branch
    )
    assert lock is None

    # Unlocking again should be a no-op
    BranchService.unlock_branch(
        session=db, project_id=project.project_id, branch=branch
    )
