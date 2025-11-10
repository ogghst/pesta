"""Cost Category model and related schemas."""

from sqlmodel import SQLModel


class CostCategoryPublic(SQLModel):
    """Public cost category schema for API responses."""

    name: str
    code: str


class CostCategoriesPublic(SQLModel):
    """Public cost categories list schema."""

    data: list[CostCategoryPublic]
    count: int
