"""Service for archiving old versions of entities."""

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import TypeVar

from sqlmodel import Session, select

from app.models import VersionStatusMixin

T = TypeVar("T", bound=VersionStatusMixin)


class VersionArchivalService:
    """Service for archiving old versions of entities."""

    @staticmethod
    def identify_versions_for_archival(
        session: Session,
        entity_class: type[T],
        retention_days: int = 365,
    ) -> Sequence[T]:
        """Identify old versions that should be archived.

        Args:
            session: Database session
            entity_class: Entity model class
            retention_days: Number of days to retain versions before archiving

        Returns:
            List of versions that should be archived
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Find versions older than cutoff that are not already archived
        statement = (
            select(entity_class)
            .where(entity_class.created_at < cutoff_date)  # type: ignore[attr-defined]
            .where(entity_class.status != "archived")  # type: ignore[attr-defined]
        )

        return session.exec(statement).all()

    @staticmethod
    def archive_versions(
        session: Session,
        entity_class: type[T],
        retention_days: int = 365,
    ) -> int:
        """Archive old versions by setting their status to 'archived'.

        Args:
            session: Database session
            entity_class: Entity model class
            retention_days: Number of days to retain versions before archiving

        Returns:
            Number of versions archived
        """
        versions_to_archive = VersionArchivalService.identify_versions_for_archival(
            session=session,
            entity_class=entity_class,
            retention_days=retention_days,
        )

        archived_count = 0
        for version in versions_to_archive:
            # Only archive if not the latest version for the entity
            entity_id = version.entity_id
            latest = session.exec(
                select(entity_class)
                .where(entity_class.entity_id == entity_id)  # type: ignore[attr-defined]
                .order_by(entity_class.version.desc())  # type: ignore[attr-defined]
            ).first()

            # Don't archive the latest version
            if latest and latest.version == version.version:
                continue

            version.status = "archived"  # type: ignore[attr-defined]
            session.add(version)
            archived_count += 1

        session.commit()
        return archived_count

    @staticmethod
    def restore_archived_version(
        session: Session,
        entity_class: type[T],
        entity_id: int | str,
        version: int,
    ) -> T | None:
        """Restore an archived version by setting its status back to 'active'.

        Args:
            session: Database session
            entity_class: Entity model class
            entity_id: Entity ID
            version: Version number to restore

        Returns:
            Restored version or None if not found
        """
        archived_version = session.exec(
            select(entity_class)
            .where(entity_class.entity_id == entity_id)  # type: ignore[attr-defined]
            .where(entity_class.version == version)  # type: ignore[attr-defined]
            .where(entity_class.status == "archived")  # type: ignore[attr-defined]
        ).first()

        if archived_version:
            archived_version.status = "active"  # type: ignore[attr-defined]
            session.add(archived_version)
            session.commit()
            return archived_version

        return None
