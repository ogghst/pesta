import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    WBE,
    CostElement,
    Message,
    Project,
    WBECreate,
    WBEPublic,
    WBEsPublic,
    WBEUpdate,
)

router = APIRouter(prefix="/wbes", tags=["wbes"])


@router.get("/", response_model=WBEsPublic)
def read_wbes(
    session: SessionDep,
    _current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    project_id: uuid.UUID | None = Query(
        default=None, description="Filter by project ID"
    ),
) -> Any:
    """
    Retrieve WBEs.
    """
    if project_id:
        # Filter by project
        count_statement = (
            select(func.count()).select_from(WBE).where(WBE.project_id == project_id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(WBE).where(WBE.project_id == project_id).offset(skip).limit(limit)
        )
    else:
        # Get all
        count_statement = select(func.count()).select_from(WBE)
        count = session.exec(count_statement).one()
        statement = select(WBE).offset(skip).limit(limit)

    wbes = session.exec(statement).all()
    return WBEsPublic(data=wbes, count=count)


@router.get("/{id}", response_model=WBEPublic)
def read_wbe(session: SessionDep, _current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get WBE by ID.
    """
    wbe = session.get(WBE, id)
    if not wbe:
        raise HTTPException(status_code=404, detail="WBE not found")
    return wbe


@router.post("/", response_model=WBEPublic)
def create_wbe(
    *, session: SessionDep, _current_user: CurrentUser, wbe_in: WBECreate
) -> Any:
    """
    Create new WBE.
    """
    # Validate that project exists
    project = session.get(Project, wbe_in.project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    wbe = WBE.model_validate(wbe_in)
    session.add(wbe)
    session.commit()
    session.refresh(wbe)
    return wbe


@router.put("/{id}", response_model=WBEPublic)
def update_wbe(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    id: uuid.UUID,
    wbe_in: WBEUpdate,
) -> Any:
    """
    Update a WBE.
    """
    wbe = session.get(WBE, id)
    if not wbe:
        raise HTTPException(status_code=404, detail="WBE not found")
    update_dict = wbe_in.model_dump(exclude_unset=True)
    wbe.sqlmodel_update(update_dict)
    session.add(wbe)
    session.commit()
    session.refresh(wbe)
    return wbe


@router.delete("/{id}")
def delete_wbe(
    session: SessionDep, _current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a WBE.
    """
    wbe = session.get(WBE, id)
    if not wbe:
        raise HTTPException(status_code=404, detail="WBE not found")

    # Check if WBE has cost elements
    ce_count = session.exec(
        select(func.count()).select_from(CostElement).where(CostElement.wbe_id == id)
    ).one()
    if ce_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete WBE with {ce_count} existing cost element(s). Delete cost elements first.",
        )

    session.delete(wbe)
    session.commit()
    return Message(message="WBE deleted successfully")
