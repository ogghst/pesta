"""Cost Categories API routes."""
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.models import CostCategoriesPublic, CostCategoryPublic

router = APIRouter(prefix="/cost-categories", tags=["cost-categories"])

# Hardcoded cost categories
COST_CATEGORIES = [
    {"name": "labor", "code": "labor"},
    {"name": "materials", "code": "materials"},
    {"name": "subcontractors", "code": "subcontractors"},
]


@router.get("/", response_model=CostCategoriesPublic)
def read_cost_categories(
    session: SessionDep,  # noqa: ARG001
    _current_user: CurrentUser,
) -> Any:
    """
    Retrieve cost categories.
    Returns hardcoded list of cost categories: labor, materials, subcontractors.
    """
    categories = [
        CostCategoryPublic(name=cat["name"], code=cat["code"])
        for cat in COST_CATEGORIES
    ]
    return CostCategoriesPublic(data=categories, count=len(categories))
