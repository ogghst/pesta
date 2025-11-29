"""Service for enforcing retention policies on soft-deleted entities."""

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import TypeVar

from sqlmodel import Session, select

from app.models import VersionStatusMixin
from app.services.entity_versioning import hard_delete_entity

T = TypeVar("T", bound=VersionStatusMixin)


class RetentionPolicyService:
    """Service for managing retention policies and permanent deletion of expired entities."""

    @staticmethod
    def identify_expired_entities(
        session: Session,
        entity_class: type[T],
        entity_type: str,
        retention_days: int = 90,
    ) -> Sequence[T]:
        """Identify entities that have been soft-deleted longer than the retention period.

        This finds entities where the latest version has status='deleted' and was created
        (i.e., soft-deleted) more than retention_days ago.

        Args:
            session: Database session
            entity_class: Entity model class
            entity_type: Entity type name (e.g., 'project', 'user')
            retention_days: Number of days to retain soft-deleted entities

        Returns:
            List of expired entities that should be permanently deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Get all deleted entities
        all_deleted = session.exec(
            select(entity_class).where(
                entity_class.status == "deleted"  # type: ignore[attr-defined]
            )
        ).all()

        # Filter to only those where the latest version (by created_at) is older than cutoff
        expired = []
        for entity in all_deleted:
            # Get the latest version for this entity_id
            entity_id = entity.entity_id
            latest = session.exec(
                select(entity_class)
                .where(entity_class.entity_id == entity_id)  # type: ignore[attr-defined]
                .order_by(entity_class.created_at.desc())  # type: ignore[attr-defined]
            ).first()

            if (
                latest
                and latest.status == "deleted"
                and latest.created_at < cutoff_date
            ):  # type: ignore[attr-defined]
                expired.append(latest)

        return expired

    @staticmethod
    def enforce_retention_policy(
        session: Session,
        entity_class: type[T],
        entity_type: str,
        retention_days: int = 90,
    ) -> int:
        """Enforce retention policy by permanently deleting expired soft-deleted entities.

        Args:
            session: Database session
            entity_class: Entity model class
            entity_type: Entity type name (e.g., 'project', 'user')
            retention_days: Number of days to retain soft-deleted entities

        Returns:
            Number of entities permanently deleted
        """
        expired_entities = RetentionPolicyService.identify_expired_entities(
            session=session,
            entity_class=entity_class,
            entity_type=entity_type,
            retention_days=retention_days,
        )

        deleted_count = 0
        pk_column = list(entity_class.__table__.primary_key.columns)[0]  # type: ignore[attr-defined]
        pk_field_name = pk_column.name

        for entity in expired_entities:
            try:
                entity_id = getattr(entity, pk_field_name)
                hard_delete_entity(
                    session=session,
                    entity_class=entity_class,
                    entity_id=entity_id,
                    entity_type=entity_type,
                )
                deleted_count += 1
            except ValueError:
                # Entity may have been deleted already or is not in deleted state
                # Skip and continue
                continue

        session.commit()
        return deleted_count
