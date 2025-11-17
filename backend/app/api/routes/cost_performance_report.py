"""Cost Performance Report API endpoints."""

import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_time_machine_control_date,
)
from app.models import Project
from app.models.cost_performance_report import CostPerformanceReportPublic
from app.services.cost_performance_report import get_cost_performance_report
from app.services.time_machine import end_of_day

router = APIRouter(prefix="/projects", tags=["reports"])


def _ensure_project_exists(session: SessionDep, project_id: uuid.UUID) -> Project:
    """Ensure project exists and return it."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get(
    "/{project_id}/reports/cost-performance",
    response_model=CostPerformanceReportPublic,
)
def get_project_cost_performance_report_endpoint(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    project_id: uuid.UUID,
    control_date: Annotated[date, Depends(get_time_machine_control_date)],
) -> Any:
    """Get cost performance report for a project.

    Returns:
        CostPerformanceReportPublic with all cost element rows and project summary.
        Each row contains all EVM metrics (PV, EV, AC, BAC, CPI, SPI, TCPI, CV, SV)
        along with hierarchical metadata (WBE, department, cost element type).
    """
    # Ensure project exists and respect time-machine
    project = _ensure_project_exists(session, project_id)
    cutoff = end_of_day(control_date)
    if project.created_at > cutoff:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get report using service function
    try:
        report = get_cost_performance_report(session, project_id, control_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return report
