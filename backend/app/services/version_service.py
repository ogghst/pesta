"""Version service for managing entity versions.

This service handles version number generation and retrieval for entities
with versioning support (VersionStatusMixin and BranchVersionMixin).
"""

import uuid

from sqlmodel import Session, func, select

from app.models import (
    WBE,
    AppConfiguration,
    AuditLog,
    BaselineCostElement,
    BaselineLog,
    BudgetAllocation,
    ChangeOrder,
    CostElement,
    CostElementSchedule,
    CostElementType,
    CostRegistration,
    Department,
    EarnedValueEntry,
    Forecast,
    Project,
    ProjectEvent,
    ProjectPhase,
    QualityEvent,
    User,
    VarianceThresholdConfig,
)

# Map entity type names to model classes
ENTITY_TYPE_MAP: dict[str, type] = {
    "wbe": WBE,
    "costelement": CostElement,
    "project": Project,
    "user": User,
    "forecast": Forecast,
    "app_configuration": AppConfiguration,
    "variance_threshold_config": VarianceThresholdConfig,
    "projectphase": ProjectPhase,
    "project_phase": ProjectPhase,
    "qualityevent": QualityEvent,
    "quality_event": QualityEvent,
    "projectevent": ProjectEvent,
    "project_event": ProjectEvent,
    "budgetallocation": BudgetAllocation,
    "budget_allocation": BudgetAllocation,
    "changeorder": ChangeOrder,
    "change_order": ChangeOrder,
    "earnedvalueentry": EarnedValueEntry,
    "earned_value_entry": EarnedValueEntry,
    "costregistration": CostRegistration,
    "cost_registration": CostRegistration,
    "costelementtype": CostElementType,
    "costelementschedule": CostElementSchedule,
    "cost_element_schedule": CostElementSchedule,
    "department": Department,
    "baselinelog": BaselineLog,
    "baseline_log": BaselineLog,
    "baselinecostelement": BaselineCostElement,
    "baseline_cost_element": BaselineCostElement,
    "auditlog": AuditLog,
    "audit_log": AuditLog,
}


class VersionService:
    """Service for managing entity versions."""

    @staticmethod
    def get_model_class(entity_type: str) -> type:
        """Get model class for entity type.

        Args:
            entity_type: Entity type name (e.g., 'wbe', 'costelement')

        Returns:
            Model class

        Raises:
            ValueError: If entity_type is not recognized
        """
        entity_type_lower = entity_type.lower()
        if entity_type_lower not in ENTITY_TYPE_MAP:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return ENTITY_TYPE_MAP[entity_type_lower]

    @staticmethod
    def get_next_version(
        session: Session,
        entity_type: str,
        entity_id: str | uuid.UUID,
        branch: str | None = None,
    ) -> int:
        """Get the next version number for an entity.

        This method queries the database to find the highest existing version
        for the entity in the specified branch, then returns the next version number.

        Args:
            session: Database session
            entity_type: Entity type name (e.g., 'wbe', 'costelement', 'project')
            entity_id: Entity ID (UUID)
            branch: Branch name (required for branch-enabled entities, None for others)

        Returns:
            Next version number (starts at 1 for new entities)

        Raises:
            ValueError: If entity_type is not recognized or branch is required but not provided
        """
        import uuid

        model_class = VersionService.get_model_class(entity_type)
        entity_id_uuid = (
            uuid.UUID(str(entity_id))
            if not isinstance(entity_id, uuid.UUID)
            else entity_id
        )

        # Determine identifier column (entity_id if available, else primary key)
        pk_column = list(model_class.__table__.primary_key.columns)[0]  # type: ignore[attr-defined]
        pk_field_name = pk_column.name
        pk_field = getattr(model_class, pk_field_name)
        entity_id_field = getattr(model_class, "entity_id", None)
        identifier_column = entity_id_field or pk_field

        # Check if model is branch-enabled
        from app.models import BranchVersionMixin

        is_branch_enabled = issubclass(model_class, BranchVersionMixin)

        if is_branch_enabled and branch is None:
            raise ValueError(
                f"Branch is required for branch-enabled entity type: {entity_type}"
            )

        # Build query to find max version
        if is_branch_enabled:
            statement = (
                select(func.max(model_class.version))  # type: ignore[attr-defined]
                .where(identifier_column == entity_id_uuid)
                .where(model_class.branch == branch)  # type: ignore[attr-defined]
            )
        else:
            statement = select(func.max(model_class.version)).where(  # type: ignore[attr-defined]
                identifier_column == entity_id_uuid
            )

        max_version = session.exec(statement).one()

        # Return next version (max_version + 1, or 1 if no versions exist)
        return (max_version or 0) + 1

    @staticmethod
    def get_current_version(
        session: Session,
        entity_type: str,
        entity_id: str | uuid.UUID,
        branch: str | None = None,
    ) -> int | None:
        """Get the current active version number for an entity.

        This method queries the database to find the active version (status='active')
        for the entity in the specified branch.

        Args:
            session: Database session
            entity_type: Entity type name (e.g., 'wbe', 'costelement', 'project')
            entity_id: Entity ID (UUID)
            branch: Branch name (required for branch-enabled entities, None for others)

        Returns:
            Current active version number, or None if no active version exists

        Raises:
            ValueError: If entity_type is not recognized or branch is required but not provided
        """
        import uuid

        model_class = VersionService.get_model_class(entity_type)
        entity_id_uuid = (
            uuid.UUID(str(entity_id))
            if not isinstance(entity_id, uuid.UUID)
            else entity_id
        )

        pk_column = list(model_class.__table__.primary_key.columns)[0]  # type: ignore[attr-defined]
        pk_field_name = pk_column.name
        pk_field = getattr(model_class, pk_field_name)
        entity_id_field = getattr(model_class, "entity_id", None)
        identifier_column = entity_id_field or pk_field

        # Check if model is branch-enabled
        from app.models import BranchVersionMixin

        is_branch_enabled = issubclass(model_class, BranchVersionMixin)

        if is_branch_enabled and branch is None:
            raise ValueError(
                f"Branch is required for branch-enabled entity type: {entity_type}"
            )

        # Build query to find active version
        if is_branch_enabled:
            statement = (
                select(model_class.version)  # type: ignore[attr-defined]
                .where(identifier_column == entity_id_uuid)
                .where(model_class.branch == branch)  # type: ignore[attr-defined]
                .where(model_class.status == "active")  # type: ignore[attr-defined]
                .order_by(model_class.version.desc())  # type: ignore[attr-defined]
                .limit(1)
            )
        else:
            statement = (
                select(model_class.version)  # type: ignore[attr-defined]
                .where(identifier_column == entity_id_uuid)
                .where(model_class.status == "active")  # type: ignore[attr-defined]
                .order_by(model_class.version.desc())  # type: ignore[attr-defined]
                .limit(1)
            )

        result = session.exec(statement).first()
        return result
