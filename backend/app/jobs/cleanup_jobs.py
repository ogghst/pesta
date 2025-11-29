"""Background jobs for cleaning up soft-deleted entities."""

import logging
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.db import engine
from app.models import BranchNotification, ChangeOrder

logger = logging.getLogger(__name__)


def cleanup_old_notifications(retention_days: int = 30) -> int:
    """Clean up old branch notifications.

    Args:
        retention_days: Number of days to retain notifications (default: 30)

    Returns:
        Number of notifications deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    deleted_count = 0

    with Session(engine) as session:
        try:
            old_notifications = session.exec(
                select(BranchNotification).where(
                    BranchNotification.created_at < cutoff_date
                )
            ).all()

            for notification in old_notifications:
                session.delete(notification)
                deleted_count += 1

            session.commit()
            logger.info(f"Cleaned up {deleted_count} old branch notifications")
        except Exception as exc:
            logger.error(f"Error cleaning up notifications: {exc}", exc_info=True)
            session.rollback()
            raise

    return deleted_count


def cleanup_merged_change_orders(retention_days: int = 90) -> int:
    """Clean up change orders that have been merged for longer than retention period.

    Args:
        retention_days: Number of days to retain merged change orders (default: 90)

    Returns:
        Number of change orders soft-deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    deleted_count = 0

    with Session(engine) as session:
        try:
            # Find change orders that are merged and created before cutoff
            # Note: We use created_at as proxy since ChangeOrder doesn't have updated_at
            merged_orders = session.exec(
                select(ChangeOrder)
                .where(ChangeOrder.workflow_status == "merged")
                .where(ChangeOrder.created_at < cutoff_date)  # type: ignore[attr-defined]
            ).all()

            from app.services.entity_versioning import soft_delete_entity

            for change_order in merged_orders:
                try:
                    # Only soft-delete if not already deleted
                    if change_order.status != "deleted":  # type: ignore[attr-defined]
                        soft_delete_entity(
                            session=session,
                            entity_class=ChangeOrder,
                            entity_id=change_order.change_order_id,
                            entity_type="changeorder",
                        )
                        deleted_count += 1
                except ValueError:
                    # Entity may already be deleted or not found
                    continue

            session.commit()
            logger.info(f"Soft-deleted {deleted_count} old merged change orders")
        except Exception as exc:
            logger.error(f"Error cleaning up change orders: {exc}", exc_info=True)
            session.rollback()
            raise

    return deleted_count


def run_cleanup_jobs() -> dict[str, int]:
    """Run all cleanup jobs.

    Returns:
        Dictionary with counts of cleaned up items per job type
    """
    results: dict[str, int] = {}

    logger.info(f"Starting cleanup jobs at {datetime.utcnow()}")

    try:
        results["notifications"] = cleanup_old_notifications()
        results["change_orders"] = cleanup_merged_change_orders()

        logger.info(f"Cleanup jobs completed. Results: {results}")
    except Exception as exc:
        logger.error(f"Error running cleanup jobs: {exc}", exc_info=True)
        raise

    return results
