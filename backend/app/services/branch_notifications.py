"""Service helpers for branch notifications."""

import uuid
from collections.abc import Sequence

from sqlmodel import Session, select

from app.models import BranchNotification


class BranchNotificationsService:
    """Encapsulates persistence logic for branch notifications."""

    @staticmethod
    def create_notification(
        *,
        session: Session,
        project_id: uuid.UUID,
        branch: str,
        event_type: str,
        message: str,
        recipients: list[str],
        context: dict | None = None,
    ) -> BranchNotification:
        """Persist a notification describing a branch event."""
        notification = BranchNotification(
            project_id=project_id,
            branch=branch,
            event_type=event_type,
            message=message,
            recipients=recipients,
            context=context or {},
        )
        session.add(notification)
        session.flush()
        return notification

    @staticmethod
    def list_notifications(
        *, session: Session, project_id: uuid.UUID, limit: int = 20
    ) -> Sequence[BranchNotification]:
        """Return the latest notifications for the given project."""
        statement = (
            select(BranchNotification)
            .where(BranchNotification.project_id == project_id)
            .order_by(BranchNotification.created_at.desc())
            .limit(limit)
        )
        return session.exec(statement).all()
