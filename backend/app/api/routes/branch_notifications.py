"""Branch notifications API routes."""

import uuid

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.models import BranchNotificationPublic, BranchNotificationsPublic
from app.services.branch_notifications import BranchNotificationsService

router = APIRouter(
    prefix="/projects/{project_id}/notifications", tags=["branch-notifications"]
)


@router.get("/", response_model=BranchNotificationsPublic)
def list_branch_notifications(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    project_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
) -> BranchNotificationsPublic:
    """Return the latest notifications for a project."""
    notifications = BranchNotificationsService.list_notifications(
        session=session, project_id=project_id, limit=limit
    )
    data = [
        BranchNotificationPublic.model_validate(notification)
        for notification in notifications
    ]
    return BranchNotificationsPublic(data=data, count=len(data))
