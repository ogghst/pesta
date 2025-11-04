"""Cost Registrations API routes."""
import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    CostElement,
    CostElementSchedule,
    CostRegistration,
    CostRegistrationCreate,
    CostRegistrationPublic,
    CostRegistrationsPublic,
    CostRegistrationUpdate,
    Message,
)

router = APIRouter(prefix="/cost-registrations", tags=["cost-registrations"])

# Valid cost categories (from cost categories endpoint)
VALID_COST_CATEGORIES = ["labor", "materials", "subcontractors"]


def validate_cost_element_exists(
    session: Session,
    cost_element_id: uuid.UUID,
) -> CostElement:
    """
    Validate that cost element exists.
    Raises HTTPException(400) if cost element not found.

    Args:
        session: Database session
        cost_element_id: ID of the cost element to validate

    Returns:
        CostElement if found
    """
    cost_element = session.get(CostElement, cost_element_id)
    if not cost_element:
        raise HTTPException(status_code=400, detail="Cost element not found")
    return cost_element


def validate_cost_category(cost_category: str) -> None:
    """
    Validate that cost category is valid.
    Raises HTTPException(400) if category is invalid.

    Args:
        cost_category: Cost category to validate
    """
    if cost_category not in VALID_COST_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cost category. Must be one of: {', '.join(VALID_COST_CATEGORIES)}",
        )


def validate_amount(amount: Decimal) -> None:
    """
    Validate that amount is positive.
    Raises HTTPException(400) if amount is invalid.

    Args:
        amount: Amount to validate
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")


def get_cost_element_schedule(
    session: Session,
    cost_element_id: uuid.UUID,
) -> CostElementSchedule | None:
    """
    Get the latest schedule for a cost element.
    Returns None if no schedule exists.

    Args:
        session: Database session
        cost_element_id: ID of the cost element

    Returns:
        CostElementSchedule or None
    """
    statement = select(CostElementSchedule).where(
        CostElementSchedule.cost_element_id == cost_element_id
    )
    return session.exec(statement).first()


@router.get("/", response_model=CostRegistrationsPublic)
def read_cost_registrations(
    session: SessionDep,
    _current_user: CurrentUser,
    cost_element_id: uuid.UUID | None = Query(
        default=None, description="Filter by cost element ID"
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> Any:
    """
    Retrieve cost registrations.
    Optionally filter by cost_element_id.
    """
    statement = select(CostRegistration)
    count_statement = select(func.count()).select_from(CostRegistration)

    if cost_element_id:
        statement = statement.where(CostRegistration.cost_element_id == cost_element_id)
        count_statement = count_statement.where(
            CostRegistration.cost_element_id == cost_element_id
        )

    # Get count
    count = session.exec(count_statement).one()

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    cost_registrations = session.exec(statement).all()

    return CostRegistrationsPublic(
        data=[CostRegistrationPublic.model_validate(cr) for cr in cost_registrations],
        count=count,
    )


@router.get("/{id}", response_model=CostRegistrationPublic)
def read_cost_registration(
    session: SessionDep, _current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get a single cost registration by ID.
    """
    cost_registration = session.get(CostRegistration, id)
    if not cost_registration:
        raise HTTPException(status_code=404, detail="Cost registration not found")
    return cost_registration


@router.post("/", response_model=CostRegistrationPublic)
def create_cost_registration(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    cost_registration_in: CostRegistrationCreate,
) -> Any:
    """
    Create a new cost registration.
    """
    # Validate cost element exists
    validate_cost_element_exists(session, cost_registration_in.cost_element_id)

    # Validate cost category
    validate_cost_category(cost_registration_in.cost_category)

    # Validate amount
    validate_amount(cost_registration_in.amount)

    # Create cost registration with created_by_id from current user
    cost_registration_data = cost_registration_in.model_dump()
    cost_registration_data["created_by_id"] = current_user.id
    cost_registration = CostRegistration.model_validate(cost_registration_data)
    session.add(cost_registration)
    session.commit()
    session.refresh(cost_registration)
    return cost_registration


@router.put("/{id}", response_model=CostRegistrationPublic)
def update_cost_registration(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    id: uuid.UUID,
    cost_registration_in: CostRegistrationUpdate,
) -> Any:
    """
    Update a cost registration.
    """
    cost_registration = session.get(CostRegistration, id)
    if not cost_registration:
        raise HTTPException(status_code=404, detail="Cost registration not found")

    update_dict = cost_registration_in.model_dump(exclude_unset=True)

    # Validate cost category if being updated
    if "cost_category" in update_dict:
        validate_cost_category(update_dict["cost_category"])

    # Validate amount if being updated
    if "amount" in update_dict:
        validate_amount(update_dict["amount"])

    # Validate cost element if being updated
    if "cost_element_id" in update_dict:
        validate_cost_element_exists(session, update_dict["cost_element_id"])

    cost_registration.sqlmodel_update(update_dict)
    session.add(cost_registration)
    session.commit()
    session.refresh(cost_registration)
    return cost_registration


@router.delete("/{id}")
def delete_cost_registration(
    session: SessionDep, _current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a cost registration.
    """
    cost_registration = session.get(CostRegistration, id)
    if not cost_registration:
        raise HTTPException(status_code=404, detail="Cost registration not found")
    session.delete(cost_registration)
    session.commit()
    return Message(message="Cost registration deleted successfully")
