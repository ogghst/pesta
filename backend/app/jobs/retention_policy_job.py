"""Background job for enforcing retention policies."""

import logging
from datetime import datetime

from sqlmodel import Session

from app.core.db import engine
from app.models import WBE, CostElement, Project
from app.services.retention_policy_service import RetentionPolicyService

logger = logging.getLogger(__name__)


def run_retention_policy_job(retention_days: int = 90) -> dict[str, int]:
    """Run retention policy enforcement for all entity types.

    This job identifies and permanently deletes soft-deleted entities that have
    exceeded the retention period.

    Args:
        retention_days: Number of days to retain soft-deleted entities (default: 90)

    Returns:
        Dictionary with counts of deleted entities per entity type
    """
    results: dict[str, int] = {}

    with Session(engine) as session:
        try:
            # Enforce retention for Projects
            logger.info(
                f"Running retention policy for Projects (retention: {retention_days} days)"
            )
            project_count = RetentionPolicyService.enforce_retention_policy(
                session=session,
                entity_class=Project,
                entity_type="project",
                retention_days=retention_days,
            )
            results["projects"] = project_count
            logger.info(f"Permanently deleted {project_count} expired projects")

            # Enforce retention for WBEs
            logger.info(
                f"Running retention policy for WBEs (retention: {retention_days} days)"
            )
            wbe_count = RetentionPolicyService.enforce_retention_policy(
                session=session,
                entity_class=WBE,
                entity_type="wbe",
                retention_days=retention_days,
            )
            results["wbes"] = wbe_count
            logger.info(f"Permanently deleted {wbe_count} expired WBEs")

            # Enforce retention for CostElements
            logger.info(
                f"Running retention policy for CostElements (retention: {retention_days} days)"
            )
            cost_element_count = RetentionPolicyService.enforce_retention_policy(
                session=session,
                entity_class=CostElement,
                entity_type="costelement",
                retention_days=retention_days,
            )
            results["cost_elements"] = cost_element_count
            logger.info(
                f"Permanently deleted {cost_element_count} expired cost elements"
            )

            logger.info(
                f"Retention policy job completed at {datetime.utcnow()}. "
                f"Results: {results}"
            )

        except Exception as exc:
            logger.error(f"Error running retention policy job: {exc}", exc_info=True)
            raise

    return results
