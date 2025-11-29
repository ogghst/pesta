"""Branch management API routes for locking and unlocking branches."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_user_project_manager_or_admin,
)
from app.models import AuditLog, BranchLock, Project, User
from app.services.branch_service import BranchService

router = APIRouter(prefix="/projects/{project_id}/branches", tags=["branches"])


def _ensure_project_exists(session: Session, project_id: uuid.UUID) -> Project:
    """Ensure project exists and return it."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


class BranchLockRequest(BaseModel):
    """Request schema for locking a branch."""

    reason: str | None = None


class BranchLockPublic(BaseModel):
    """Public schema for branch lock information."""

    lock_id: str
    project_id: str
    branch: str
    locked_by_id: str
    locked_by_name: str | None
    reason: str | None
    locked_at: str


@router.post("/{branch}/lock", response_model=BranchLockPublic)
def lock_branch(
    *,
    session: SessionDep,
    current_user: Annotated[
        CurrentUser, Depends(get_current_user_project_manager_or_admin)
    ],
    project_id: uuid.UUID,
    branch: str,
    lock_request: BranchLockRequest,
) -> Any:
    """
    Lock a branch to prevent modifications.

    Only project managers and admins can lock branches.
    Main branch cannot be locked.
    """
    _ensure_project_exists(session, project_id)

    try:
        lock = BranchService.lock_branch(
            session=session,
            project_id=project_id,
            branch=branch,
            locked_by_id=current_user.id,
            reason=lock_request.reason,
        )
        session.flush()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create audit log entry (after lock is created so we can use lock_id)
    # Audit logs are immutable records and do not use versioning
    audit_log = AuditLog(
        entity_type="branch_lock",
        entity_id=lock.lock_id,  # Reference the audited entity (the lock)
        action="lock",
        user_id=current_user.id,
        reason=lock_request.reason,
        new_value=f"Branch {branch} locked",
    )
    session.add(audit_log)
    session.flush()

    session.commit()
    session.refresh(lock)

    # Get locked by user name
    locked_by_user = session.get(User, lock.locked_by_id)
    locked_by_name = locked_by_user.full_name if locked_by_user else None

    return BranchLockPublic(
        lock_id=str(lock.lock_id),
        project_id=str(lock.project_id),
        branch=lock.branch,
        locked_by_id=str(lock.locked_by_id),
        locked_by_name=locked_by_name,
        reason=lock.reason,
        locked_at=lock.locked_at.isoformat(),
    )


@router.delete("/{branch}/lock")
def unlock_branch(
    *,
    session: SessionDep,
    current_user: Annotated[
        CurrentUser, Depends(get_current_user_project_manager_or_admin)
    ],
    project_id: uuid.UUID,
    branch: str,
) -> dict[str, str]:
    """
    Unlock a branch to allow modifications.

    Only project managers and admins can unlock branches.
    """
    _ensure_project_exists(session, project_id)

    # Get lock info before unlocking (for audit log)
    lock = BranchService.get_branch_lock(session, project_id, branch)
    if not lock:
        raise HTTPException(status_code=404, detail="Branch is not locked")

    lock_id = lock.lock_id  # Save lock_id before unlocking

    BranchService.unlock_branch(session=session, project_id=project_id, branch=branch)
    session.flush()

    # Create audit log entry
    # Audit logs are immutable records and do not use versioning
    audit_log = AuditLog(
        entity_type="branch_lock",
        entity_id=lock_id,  # Reference the audited entity (the lock)
        action="unlock",
        user_id=current_user.id,
        new_value=f"Branch {branch} unlocked",
    )
    session.add(audit_log)
    session.flush()

    session.commit()

    return {"message": f"Branch {branch} unlocked successfully"}


@router.get("/{branch}/lock")
def get_branch_lock_status(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    project_id: uuid.UUID,
    branch: str,
) -> Any:
    """
    Get lock status for a specific branch.

    Returns lock information if branch is locked, None otherwise.
    """
    _ensure_project_exists(session, project_id)

    lock = BranchService.get_branch_lock(session, project_id, branch)
    if not lock:
        return None

    # Get locked by user name
    locked_by_user = session.get(User, lock.locked_by_id)
    locked_by_name = locked_by_user.full_name if locked_by_user else None

    return BranchLockPublic(
        lock_id=str(lock.lock_id),
        project_id=str(lock.project_id),
        branch=lock.branch,
        locked_by_id=str(lock.locked_by_id),
        locked_by_name=locked_by_name,
        reason=lock.reason,
        locked_at=lock.locked_at.isoformat(),
    )


@router.get("/locks")
def list_branch_locks(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    project_id: uuid.UUID,
) -> dict[str, list[dict[str, Any]]]:
    """
    Get lock status for all branches in a project.

    Returns a dictionary mapping branch names to their lock information.
    """
    _ensure_project_exists(session, project_id)

    # Get all locks for this project
    locks = session.exec(
        select(BranchLock).where(BranchLock.project_id == project_id)
    ).all()

    # Get all user IDs to fetch user names efficiently
    user_ids = {lock.locked_by_id for lock in locks}
    users = {}
    if user_ids:
        user_list = session.exec(select(User).where(User.id.in_(list(user_ids)))).all()
        users = {user.id: user for user in user_list}

    # Build response
    locks_dict = {}
    for lock in locks:
        locked_by_user = users.get(lock.locked_by_id)
        locked_by_name = locked_by_user.full_name if locked_by_user else None

        locks_dict[lock.branch] = {
            "lock_id": str(lock.lock_id),
            "project_id": str(lock.project_id),
            "branch": lock.branch,
            "locked_by_id": str(lock.locked_by_id),
            "locked_by_name": locked_by_name,
            "reason": lock.reason,
            "locked_at": lock.locked_at.isoformat(),
        }

    return {"locks": locks_dict}
