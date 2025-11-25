"""Branch, Version, and Status mixin for WBE and CostElement entities.

This mixin extends VersionStatusMixin and adds branch field for entities that
support branching (WBE and CostElement only).

Branching enables:
- Isolated changes in change order branches
- Merge operations from branches to main
- Branch-based versioning
"""

from sqlmodel import Field

from app.models.version_status_mixin import VersionStatusMixin


class BranchVersionMixin(VersionStatusMixin):
    """Extended mixin adding branch field for entities that support branching.

    This mixin extends VersionStatusMixin and adds a branch field. It should
    only be inherited by WBE and CostElement models.

    The branch field enables:
    - Change order branches (e.g., 'co-001', 'co-002')
    - Main branch for production data ('main')
    - Branch isolation for staged changes

    Usage:
        class WBE(WBEBase, BranchVersionMixin, table=True):
            ...
    """

    branch: str = Field(default="main", max_length=50, nullable=False)
