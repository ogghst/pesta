"""API endpoints for EVM performance indices calculations."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_time_machine_control_date,
)
from app.api.routes.earned_value import (
    _get_entry_map,
)
from app.api.routes.planned_value import (
    _get_schedule_map,
)
from app.models import (
    WBE,
    CostElement,
    CostRegistration,
    EVMIndicesProjectPublic,
    EVMIndicesWBEPublic,
    Project,
)
from app.services.earned_value import (
    aggregate_earned_value,
    calculate_cost_element_earned_value,
)
from app.services.evm_indices import (
    calculate_cpi,
    calculate_spi,
    calculate_tcpi,
)
from app.services.planned_value import (
    aggregate_planned_value,
    calculate_cost_element_planned_value,
)
from app.services.time_machine import (
    TimeMachineEventType,
    apply_time_machine_filters,
    end_of_day,
)

router = APIRouter(prefix="/projects", tags=["evm-indices"])


def _ensure_project_exists(session: SessionDep, project_id: uuid.UUID) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _ensure_wbe_exists(
    session: SessionDep, project_id: uuid.UUID, wbe_id: uuid.UUID, control_date: date
) -> WBE:
    project = _ensure_project_exists(session, project_id)
    wbe = session.get(WBE, wbe_id)
    if not wbe or wbe.project_id != project.project_id:
        raise HTTPException(status_code=404, detail="WBE not found")
    cutoff = end_of_day(control_date)
    if wbe.created_at > cutoff:
        raise HTTPException(status_code=404, detail="WBE not found")
    return wbe


def _get_wbe_evm_inputs(
    session: SessionDep, wbe_id: uuid.UUID, control_date: date
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Get PV, EV, AC, and BAC for a WBE at control date.

    Returns:
        Tuple of (planned_value, earned_value, actual_cost, budget_bac)
    """
    # Get cost elements for WBE
    cutoff = end_of_day(control_date)
    cost_elements = session.exec(
        select(CostElement).where(
            CostElement.wbe_id == wbe_id,
            CostElement.created_at <= cutoff,
        )
    ).all()

    if not cost_elements:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")

    cost_element_ids = [ce.cost_element_id for ce in cost_elements]

    # Get PV
    schedule_map = _get_schedule_map(session, cost_element_ids, control_date)
    pv_tuples: list[tuple[Decimal, Decimal]] = []
    for cost_element in cost_elements:
        pv, _ = calculate_cost_element_planned_value(
            cost_element=cost_element,
            schedule=schedule_map.get(cost_element.cost_element_id),
            control_date=control_date,
        )
        pv_tuples.append((pv, cost_element.budget_bac or Decimal("0.00")))
    pv_aggregates = aggregate_planned_value(pv_tuples)
    planned_value = pv_aggregates.planned_value

    # Get EV
    entry_map = _get_entry_map(session, cost_element_ids, control_date)
    ev_tuples: list[tuple[Decimal, Decimal]] = []
    for cost_element in cost_elements:
        entry = entry_map.get(cost_element.cost_element_id)
        if entry is None:
            continue
        ev, _ = calculate_cost_element_earned_value(
            cost_element=cost_element,
            entry=entry,
            control_date=control_date,
        )
        ev_tuples.append((ev, cost_element.budget_bac or Decimal("0.00")))
    ev_aggregates = aggregate_earned_value(ev_tuples)
    earned_value = ev_aggregates.earned_value

    # Get AC (actual cost)
    if cost_element_ids:
        statement = select(CostRegistration).where(
            CostRegistration.cost_element_id.in_(cost_element_ids),
        )
        statement = apply_time_machine_filters(
            statement, TimeMachineEventType.COST_REGISTRATION, control_date
        )
        cost_registrations = session.exec(statement).all()
        actual_cost = sum(cr.amount for cr in cost_registrations)
    else:
        actual_cost = Decimal("0.00")

    # Get BAC (budget at completion)
    budget_bac = sum(ce.budget_bac for ce in cost_elements)

    return planned_value, earned_value, actual_cost, budget_bac


def _get_project_evm_inputs(
    session: SessionDep, project_id: uuid.UUID, control_date: date
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Get PV, EV, AC, and BAC for a project at control date.

    Returns:
        Tuple of (planned_value, earned_value, actual_cost, budget_bac)
    """
    _ensure_project_exists(session, project_id)

    # Get all WBEs for project
    cutoff = end_of_day(control_date)
    wbes = session.exec(
        select(WBE).where(
            WBE.project_id == project_id,
            WBE.created_at <= cutoff,
        )
    ).all()

    if not wbes:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")

    wbe_ids = [wbe.wbe_id for wbe in wbes]

    # Get all cost elements for all WBEs
    cost_elements = session.exec(
        select(CostElement).where(
            CostElement.wbe_id.in_(wbe_ids),
            CostElement.created_at <= cutoff,
        )
    ).all()

    if not cost_elements:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")

    cost_element_ids = [ce.cost_element_id for ce in cost_elements]

    # Get PV
    schedule_map = _get_schedule_map(session, cost_element_ids, control_date)
    pv_tuples: list[tuple[Decimal, Decimal]] = []
    for cost_element in cost_elements:
        pv, _ = calculate_cost_element_planned_value(
            cost_element=cost_element,
            schedule=schedule_map.get(cost_element.cost_element_id),
            control_date=control_date,
        )
        pv_tuples.append((pv, cost_element.budget_bac or Decimal("0.00")))
    pv_aggregates = aggregate_planned_value(pv_tuples)
    planned_value = pv_aggregates.planned_value

    # Get EV
    entry_map = _get_entry_map(session, cost_element_ids, control_date)
    ev_tuples: list[tuple[Decimal, Decimal]] = []
    for cost_element in cost_elements:
        entry = entry_map.get(cost_element.cost_element_id)
        if entry is None:
            continue
        ev, _ = calculate_cost_element_earned_value(
            cost_element=cost_element,
            entry=entry,
            control_date=control_date,
        )
        ev_tuples.append((ev, cost_element.budget_bac or Decimal("0.00")))
    ev_aggregates = aggregate_earned_value(ev_tuples)
    earned_value = ev_aggregates.earned_value

    # Get AC (actual cost)
    statement = select(CostRegistration).where(
        CostRegistration.cost_element_id.in_(cost_element_ids),
    )
    statement = apply_time_machine_filters(
        statement, TimeMachineEventType.COST_REGISTRATION, control_date
    )
    cost_registrations = session.exec(statement).all()
    actual_cost = sum(cr.amount for cr in cost_registrations)

    # Get BAC (budget at completion)
    budget_bac = sum(ce.budget_bac for ce in cost_elements)

    return planned_value, earned_value, actual_cost, budget_bac


@router.get(
    "/{project_id}/evm-indices/wbes/{wbe_id}",
    response_model=EVMIndicesWBEPublic,
)
def get_wbe_evm_indices(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    project_id: uuid.UUID,
    wbe_id: uuid.UUID,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
) -> Any:
    """Get EVM performance indices (CPI, SPI, TCPI) for a WBE.

    Returns:
        EVMIndicesWBEPublic with CPI, SPI, TCPI, and underlying PV, EV, AC, BAC values.
    """
    wbe = _ensure_wbe_exists(session, project_id, wbe_id, control_date)

    pv, ev, ac, bac = _get_wbe_evm_inputs(session, wbe_id, control_date)

    # Calculate indices
    cpi = calculate_cpi(ev, ac)
    spi = calculate_spi(ev, pv)
    tcpi = calculate_tcpi(bac, ev, ac)

    return EVMIndicesWBEPublic(
        level="wbe",
        control_date=control_date,
        cpi=cpi,
        spi=spi,
        tcpi=tcpi,
        planned_value=pv,
        earned_value=ev,
        actual_cost=ac,
        budget_bac=bac,
        wbe_id=wbe.wbe_id,
    )


@router.get(
    "/{project_id}/evm-indices",
    response_model=EVMIndicesProjectPublic,
)
def get_project_evm_indices(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    project_id: uuid.UUID,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
) -> Any:
    """Get EVM performance indices (CPI, SPI, TCPI) for a project.

    Returns:
        EVMIndicesProjectPublic with CPI, SPI, TCPI, and underlying PV, EV, AC, BAC values.
    """
    project = _ensure_project_exists(session, project_id)

    pv, ev, ac, bac = _get_project_evm_inputs(session, project_id, control_date)

    # Calculate indices
    cpi = calculate_cpi(ev, ac)
    spi = calculate_spi(ev, pv)
    tcpi = calculate_tcpi(bac, ev, ac)

    return EVMIndicesProjectPublic(
        level="project",
        control_date=control_date,
        cpi=cpi,
        spi=spi,
        tcpi=tcpi,
        planned_value=pv,
        earned_value=ev,
        actual_cost=ac,
        budget_bac=bac,
        project_id=project.project_id,
    )
