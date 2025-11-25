"""App Configuration API endpoints (admin only)."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app.api.deps import SessionDep, get_current_active_admin
from app.models import (
    AppConfiguration,
    AppConfigurationCreate,
    AppConfigurationPublic,
    AppConfigurationsPublic,
    AppConfigurationUpdate,
    Message,
)
from app.services.branch_filtering import apply_status_filters
from app.services.entity_versioning import (
    create_entity_with_version,
    soft_delete_entity,
    update_entity_with_version,
)

router = APIRouter(prefix="/app-configuration", tags=["admin"])


def _get_app_configuration(
    session: Session, config_id: uuid.UUID, include_inactive: bool = False
) -> AppConfiguration:
    """Get app configuration by ID."""
    statement = select(AppConfiguration).where(AppConfiguration.config_id == config_id)
    if not include_inactive:
        statement = apply_status_filters(statement, AppConfiguration, status="active")
    config = session.exec(statement).first()
    if not config:
        raise HTTPException(status_code=404, detail="App configuration not found")
    return config


@router.get("/", response_model=AppConfigurationsPublic)
def list_app_configurations(
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """List all app configurations (admin only)."""
    count_statement = select(func.count()).select_from(AppConfiguration)
    count_statement = apply_status_filters(
        count_statement, AppConfiguration, status="active"
    )
    count = session.exec(count_statement).one()

    statement = select(AppConfiguration).order_by(
        AppConfiguration.config_key, AppConfiguration.created_at.desc()
    )
    statement = apply_status_filters(statement, AppConfiguration, status="active")
    configs = session.exec(statement).all()

    return AppConfigurationsPublic(data=configs, count=count)


@router.get("/{config_id}", response_model=AppConfigurationPublic)
def get_app_configuration(
    config_id: uuid.UUID,
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """Get an app configuration by ID (admin only)."""
    config = _get_app_configuration(session, config_id)
    return config


@router.post("/", response_model=AppConfigurationPublic)
def create_app_configuration(
    config_in: AppConfigurationCreate,
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """Create a new app configuration (admin only)."""
    # Check if config_key already exists
    statement = select(AppConfiguration).where(
        AppConfiguration.config_key == config_in.config_key
    )
    statement = apply_status_filters(statement, AppConfiguration, status="active")
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration with key '{config_in.config_key}' already exists",
        )

    # Create new configuration
    config = AppConfiguration.model_validate(config_in)
    config = create_entity_with_version(
        session=session,
        entity=config,
        entity_type="app_configuration",
        entity_id=str(config.config_id),
    )
    session.commit()
    session.refresh(config)

    return config


@router.patch("/{config_id}", response_model=AppConfigurationPublic)
def update_app_configuration(
    config_id: uuid.UUID,
    config_update: AppConfigurationUpdate,
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """Update an app configuration (admin only)."""
    config = _get_app_configuration(session, config_id)

    # If updating config_key, check for uniqueness
    if (
        config_update.config_key is not None
        and config_update.config_key != config.config_key
    ):
        statement = select(AppConfiguration).where(
            AppConfiguration.config_key == config_update.config_key,
            AppConfiguration.config_id != config_id,
        )
        statement = apply_status_filters(statement, AppConfiguration, status="active")
        existing = session.exec(statement).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Configuration with key '{config_update.config_key}' already exists",
            )

    update_data = config_update.model_dump(exclude_unset=True)
    config = update_entity_with_version(
        session=session,
        entity_class=AppConfiguration,
        entity_id=config_id,
        update_data=update_data,
        entity_type="app_configuration",
    )
    session.commit()
    session.refresh(config)

    return config


@router.delete("/{config_id}", response_model=Message)
def delete_app_configuration(
    config_id: uuid.UUID,
    session: SessionDep,
    _current_user: Annotated[Any, Depends(get_current_active_admin)],
) -> Any:
    """Delete an app configuration (admin only)."""
    _get_app_configuration(session, config_id)
    soft_delete_entity(
        session=session,
        entity_class=AppConfiguration,
        entity_id=config_id,
        entity_type="app_configuration",
    )
    session.commit()

    return Message(message="App configuration deleted successfully")
