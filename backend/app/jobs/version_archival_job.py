"""Background job for archiving old versions."""

import logging
from datetime import datetime

from sqlmodel import Session

from app.core.db import engine
from app.models import WBE, CostElement, Project
from app.services.version_archival_service import VersionArchivalService

logger = logging.getLogger(__name__)


def run_version_archival_job(retention_days: int = 365) -> dict[str, int]:
    """Run version archival for all entity types.

    This job identifies and archives old versions of entities that have exceeded
    the retention period.

    Args:
        retention_days: Number of days to retain versions before archiving (default: 365)

    Returns:
        Dictionary with counts of archived versions per entity type
    """
    results: dict[str, int] = {}

    with Session(engine) as session:
        try:
            # Archive old Project versions
            logger.info(
                f"Running version archival for Projects (retention: {retention_days} days)"
            )
            project_count = VersionArchivalService.archive_versions(
                session=session,
                entity_class=Project,
                retention_days=retention_days,
            )
            results["projects"] = project_count
            logger.info(f"Archived {project_count} old project versions")

            # Archive old WBE versions
            logger.info(
                f"Running version archival for WBEs (retention: {retention_days} days)"
            )
            wbe_count = VersionArchivalService.archive_versions(
                session=session,
                entity_class=WBE,
                retention_days=retention_days,
            )
            results["wbes"] = wbe_count
            logger.info(f"Archived {wbe_count} old WBE versions")

            # Archive old CostElement versions
            logger.info(
                f"Running version archival for CostElements (retention: {retention_days} days)"
            )
            cost_element_count = VersionArchivalService.archive_versions(
                session=session,
                entity_class=CostElement,
                retention_days=retention_days,
            )
            results["cost_elements"] = cost_element_count
            logger.info(f"Archived {cost_element_count} old cost element versions")

            logger.info(
                f"Version archival job completed at {datetime.utcnow()}. "
                f"Results: {results}"
            )

        except Exception as exc:
            logger.error(f"Error running version archival job: {exc}", exc_info=True)
            raise

    return results
