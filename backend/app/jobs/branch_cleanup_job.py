"""Background job for cleaning up merged/cancelled branches."""

import logging
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.db import engine
from app.models import ChangeOrder
from app.services.branch_service import BranchService

logger = logging.getLogger(__name__)


def cleanup_merged_branches(retention_days: int = 30) -> int:
    """Clean up branches that have been merged for longer than retention period.

    Args:
        retention_days: Number of days to retain merged branches (default: 30)

    Returns:
        Number of branches soft-deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    deleted_count = 0

    with Session(engine) as session:
        try:
            # Find change orders with merged workflow status that are old
            merged_change_orders = session.exec(
                select(ChangeOrder)
                .where(ChangeOrder.workflow_status == "merged")
                .where(ChangeOrder.created_at < cutoff_date)  # type: ignore[attr-defined]
                .where(ChangeOrder.branch.isnot(None))  # type: ignore[attr-defined]
            ).all()

            for change_order in merged_change_orders:
                if (
                    change_order.branch
                    and change_order.branch != BranchService.MAIN_BRANCH
                ):
                    try:
                        BranchService.delete_branch(
                            session=session, branch=change_order.branch
                        )
                        deleted_count += 1
                        logger.info(
                            f"Soft-deleted merged branch: {change_order.branch}"
                        )
                    except ValueError as exc:
                        logger.warning(
                            f"Could not delete branch {change_order.branch}: {exc}"
                        )
                        continue

            session.commit()
            logger.info(f"Soft-deleted {deleted_count} merged branches")
        except Exception as exc:
            logger.error(f"Error cleaning up merged branches: {exc}", exc_info=True)
            session.rollback()
            raise

    return deleted_count


def cleanup_cancelled_branches(retention_days: int = 7) -> int:
    """Clean up branches for cancelled change orders.

    Args:
        retention_days: Number of days to retain cancelled branches (default: 7)

    Returns:
        Number of branches soft-deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    deleted_count = 0

    with Session(engine) as session:
        try:
            # Find change orders with cancelled workflow status
            cancelled_change_orders = session.exec(
                select(ChangeOrder)
                .where(ChangeOrder.workflow_status == "cancelled")
                .where(ChangeOrder.created_at < cutoff_date)  # type: ignore[attr-defined]
                .where(ChangeOrder.branch.isnot(None))  # type: ignore[attr-defined]
            ).all()

            for change_order in cancelled_change_orders:
                if (
                    change_order.branch
                    and change_order.branch != BranchService.MAIN_BRANCH
                ):
                    try:
                        BranchService.delete_branch(
                            session=session, branch=change_order.branch
                        )
                        deleted_count += 1
                        logger.info(
                            f"Soft-deleted cancelled branch: {change_order.branch}"
                        )
                    except ValueError as exc:
                        logger.warning(
                            f"Could not delete branch {change_order.branch}: {exc}"
                        )
                        continue

            session.commit()
            logger.info(f"Soft-deleted {deleted_count} cancelled branches")
        except Exception as exc:
            logger.error(f"Error cleaning up cancelled branches: {exc}", exc_info=True)
            session.rollback()
            raise

    return deleted_count


def run_branch_cleanup_job() -> dict[str, int]:
    """Run all branch cleanup jobs.

    Returns:
        Dictionary with counts of cleaned up branches per type
    """
    results: dict[str, int] = {}

    logger.info(f"Starting branch cleanup jobs at {datetime.utcnow()}")

    try:
        results["merged"] = cleanup_merged_branches()
        results["cancelled"] = cleanup_cancelled_branches()

        logger.info(f"Branch cleanup jobs completed. Results: {results}")
    except Exception as exc:
        logger.error(f"Error running branch cleanup jobs: {exc}", exc_info=True)
        raise

    return results
