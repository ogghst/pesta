"""Variance Threshold Configuration API endpoints."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app.api.deps import SessionDep, get_current_active_admin
from app.models import (
    Message,
    VarianceThresholdConfig,
    VarianceThresholdConfigCreate,
    VarianceThresholdConfigPublic,
    VarianceThresholdConfigsPublic,
    VarianceThresholdConfigUpdate,
)
from app.services.branch_filtering import apply_status_filters
from app.services.entity_versioning import (
    create_entity_with_version,
    soft_delete_entity,
    update_entity_with_version,
)

router = APIRouter(prefix="/variance-threshold-configs", tags=["admin"])


def _get_variance_threshold_config(
    session: Session, config_id: uuid.UUID, include_inactive: bool = False
) -> VarianceThresholdConfig:
    """Get variance threshold configuration by ID."""
    statement = select(VarianceThresholdConfig).where(
        VarianceThresholdConfig.variance_threshold_config_id == config_id
    )
    if not include_inactive:
        statement = apply_status_filters(
            statement, VarianceThresholdConfig, status="active"
        )
    config = session.exec(statement).first()
    if not config:
        raise HTTPException(
            status_code=404, detail="Variance threshold configuration not found"
        )
    return config


@router.get("/", response_model=VarianceThresholdConfigsPublic)
def list_variance_threshold_configs(
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """List all variance threshold configurations (admin only)."""
    count_statement = select(func.count()).select_from(VarianceThresholdConfig)
    count_statement = apply_status_filters(
        count_statement, VarianceThresholdConfig, status="active"
    )
    count = session.exec(count_statement).one()

    statement = select(VarianceThresholdConfig).order_by(
        VarianceThresholdConfig.threshold_type,
        VarianceThresholdConfig.created_at.desc(),
    )
    statement = apply_status_filters(
        statement, VarianceThresholdConfig, status="active"
    )
    configs = session.exec(statement).all()

    return VarianceThresholdConfigsPublic(data=configs, count=count)


@router.get("/{config_id}", response_model=VarianceThresholdConfigPublic)
def get_variance_threshold_config(
    config_id: uuid.UUID,
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """Get a variance threshold configuration by ID (admin only)."""
    config = _get_variance_threshold_config(session, config_id)
    return config


@router.post("/", response_model=VarianceThresholdConfigPublic)
def create_variance_threshold_config(
    config_in: VarianceThresholdConfigCreate,
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """Create a new variance threshold configuration (admin only).

    If creating an active threshold, any existing active threshold of the same type
    will be deactivated.
    """
    # If creating an active threshold, deactivate existing active one of same type
    if config_in.is_active:
        statement = select(VarianceThresholdConfig).where(
            VarianceThresholdConfig.threshold_type == config_in.threshold_type,
            VarianceThresholdConfig.is_active == True,  # noqa: E712
        )
        statement = apply_status_filters(
            statement, VarianceThresholdConfig, status="active"
        )
        existing_active = session.exec(statement).first()
        if existing_active:
            update_entity_with_version(
                session=session,
                entity_class=VarianceThresholdConfig,
                entity_id=existing_active.variance_threshold_config_id,
                update_data={"is_active": False},
                entity_type="variance_threshold_config",
            )

    # Create new configuration
    config = VarianceThresholdConfig.model_validate(config_in)
    config = create_entity_with_version(
        session=session,
        entity=config,
        entity_type="variance_threshold_config",
        entity_id=str(config.variance_threshold_config_id),
    )
    session.commit()
    session.refresh(config)

    return config


@router.put("/{config_id}", response_model=VarianceThresholdConfigPublic)
def update_variance_threshold_config(
    config_id: uuid.UUID,
    config_update: VarianceThresholdConfigUpdate,
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """Update a variance threshold configuration (admin only).

    If updating to active, any existing active threshold of the same type
    will be deactivated.
    """
    config = _get_variance_threshold_config(session, config_id)

    # If updating to active, deactivate existing active one of same type (if different)
    update_data = config_update.model_dump(exclude_unset=True)
    target_type = update_data.get("threshold_type", config.threshold_type)
    target_is_active = update_data.get("is_active")
    if target_is_active is None:
        target_is_active = config.is_active

    if target_is_active:
        statement = select(VarianceThresholdConfig).where(
            VarianceThresholdConfig.threshold_type == target_type,
            VarianceThresholdConfig.is_active == True,  # noqa: E712
            VarianceThresholdConfig.variance_threshold_config_id != config_id,
        )
        statement = apply_status_filters(
            statement, VarianceThresholdConfig, status="active"
        )
        existing_active = session.exec(statement).first()
        if existing_active:
            update_entity_with_version(
                session=session,
                entity_class=VarianceThresholdConfig,
                entity_id=existing_active.variance_threshold_config_id,
                update_data={"is_active": False},
                entity_type="variance_threshold_config",
            )

    config = update_entity_with_version(
        session=session,
        entity_class=VarianceThresholdConfig,
        entity_id=config_id,
        update_data=update_data,
        entity_type="variance_threshold_config",
    )
    session.commit()
    session.refresh(config)

    return config


@router.delete("/{config_id}", response_model=Message)
def delete_variance_threshold_config(
    config_id: uuid.UUID,
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """Delete a variance threshold configuration (admin only)."""
    _get_variance_threshold_config(session, config_id)
    soft_delete_entity(
        session=session,
        entity_class=VarianceThresholdConfig,
        entity_id=config_id,
        entity_type="variance_threshold_config",
    )
    session.commit()

    return Message(message="Variance threshold configuration deleted successfully")
