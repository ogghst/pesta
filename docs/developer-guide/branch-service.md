# Branch Service Developer Guide

**Last Updated:** November 29, 2025

## Overview

The `BranchService` provides core functionality for managing branches in BackCast. This guide explains how to use the service and extend it.

## Service Overview

The `BranchService` is located at `app/services/branch_service.py` and provides:

- Branch creation
- Branch merging
- Branch deletion
- Branch cloning
- Branch locking
- Branch comparison

## Core Methods

### create_branch()

Creates a new branch for a change order.

```python
from app.services.branch_service import BranchService

branch_name = BranchService.create_branch(
    session=session,
    change_order_id=change_order_id,
)
# Returns: "co-001" (or similar)
```

**Parameters:**
- `session: Session`: Database session
- `change_order_id: UUID`: Change order to create branch for

**Returns:**
- `str`: Branch name (e.g., "co-001")

**Behavior:**
- Generates unique branch name
- Associates branch with change order
- Creates initial branch data (copies from main if needed)

### merge_branch()

Merges a branch into main.

```python
result = BranchService.merge_branch(
    session=session,
    project_id=project_id,
    branch="co-001",
    merge_strategy="theirs",  # or "ours", "manual"
)
```

**Parameters:**
- `session: Session`: Database session
- `project_id: UUID`: Project ID
- `branch: str`: Branch name to merge
- `merge_strategy: str`: Conflict resolution strategy

**Returns:**
- `dict`: Merge result with statistics

**Behavior:**
- Identifies all changes in branch
- Detects conflicts with main
- Resolves conflicts based on strategy
- Applies changes to main
- Soft-deletes branch

### delete_branch()

Soft-deletes a branch.

```python
BranchService.delete_branch(
    session=session,
    project_id=project_id,
    branch="co-001",
)
```

**Parameters:**
- `session: Session`: Database session
- `project_id: UUID`: Project ID
- `branch: str`: Branch name to delete

**Behavior:**
- Soft-deletes all entities in branch
- Updates branch status
- Sends notifications

### clone_branch()

Creates a copy of a branch.

```python
new_branch = BranchService.clone_branch(
    session=session,
    project_id=project_id,
    source_branch="co-001",
    target_branch="co-002",  # Optional, auto-generated if not provided
)
```

**Parameters:**
- `session: Session`: Database session
- `project_id: UUID`: Project ID
- `source_branch: str`: Branch to clone
- `target_branch: str | None`: Name for new branch (optional)

**Returns:**
- `str`: New branch name

**Behavior:**
- Copies all entities from source branch
- Creates new branch with copied data
- Preserves entity relationships

### lock_branch()

Locks a branch to prevent modifications.

```python
BranchService.lock_branch(
    session=session,
    project_id=project_id,
    branch="co-001",
    locked_by_id=user_id,
    reason="Under review",
)
```

**Parameters:**
- `session: Session`: Database session
- `project_id: UUID`: Project ID
- `branch: str`: Branch name
- `locked_by_id: UUID`: User locking the branch
- `reason: str`: Reason for locking

**Behavior:**
- Creates branch lock record
- Prevents modifications to branch
- Sends notifications

### unlock_branch()

Unlocks a branch.

```python
BranchService.unlock_branch(
    session=session,
    project_id=project_id,
    branch="co-001",
    unlocked_by_id=user_id,
)
```

**Parameters:**
- `session: Session`: Database session
- `project_id: UUID`: Project ID
- `branch: str`: Branch name
- `unlocked_by_id: UUID`: User unlocking the branch

**Behavior:**
- Removes branch lock
- Allows modifications
- Sends notifications

## Branch Comparison

### compare_branches()

Compares two branches to identify differences.

```python
comparison = BranchService.compare_branches(
    session=session,
    project_id=project_id,
    branch="co-001",
    base_branch="main",
)
```

**Returns:**
```python
{
    "creates": [...],  # New entities in branch
    "updates": [...],  # Modified entities
    "deletes": [...],  # Deleted entities
    "financial_impact": {
        "total_budget_change": Decimal("1000.00"),
        "total_revenue_change": Decimal("500.00"),
    },
}
```

## Integration Patterns

### Creating a Change Order with Branch

```python
# 1. Create change order
change_order = ChangeOrder(
    project_id=project_id,
    change_order_number="CO-001",
    # ... other fields
)
session.add(change_order)
session.commit()

# 2. Create branch
branch_name = BranchService.create_branch(
    session=session,
    change_order_id=change_order.change_order_id,
)

# 3. Associate branch with change order
change_order.branch = branch_name
session.commit()
```

### Merging a Branch

```python
# 1. Compare branches first
comparison = BranchService.compare_branches(
    session=session,
    project_id=project_id,
    branch="co-001",
    base_branch="main",
)

# 2. Check for conflicts
if comparison.get("conflicts"):
    # Handle conflicts
    pass

# 3. Merge branch
result = BranchService.merge_branch(
    session=session,
    project_id=project_id,
    branch="co-001",
    merge_strategy="theirs",
)

# 4. Send notifications
BranchNotificationsService.create_notification(
    session=session,
    project_id=project_id,
    branch="co-001",
    event_type="merge_completed",
    message=f"Branch {branch} merged successfully",
    recipients=[...],
)
```

## Error Handling

### Common Exceptions

```python
from app.services.branch_service import BranchService
from app.exceptions import BranchNotFoundError, BranchLockedError

try:
    BranchService.merge_branch(...)
except BranchNotFoundError:
    # Branch doesn't exist
    pass
except BranchLockedError:
    # Branch is locked
    pass
```

## Testing

### Unit Tests

```python
def test_create_branch(db: Session):
    change_order = create_test_change_order(db)
    branch = BranchService.create_branch(
        session=db,
        change_order_id=change_order.change_order_id,
    )
    assert branch.startswith("co-")
```

### Integration Tests

```python
def test_merge_branch_flow(db: Session):
    # Create branch
    branch = BranchService.create_branch(...)

    # Make changes in branch
    # ...

    # Merge branch
    result = BranchService.merge_branch(...)

    # Verify merge
    assert result["creates"] > 0
```

## Extending the Service

### Adding Custom Branch Operations

```python
class BranchService:
    @staticmethod
    def custom_operation(
        session: Session,
        project_id: UUID,
        branch: str,
    ) -> dict:
        """Custom branch operation."""
        # Implementation
        pass
```

### Adding Branch Validation

```python
class BranchService:
    @staticmethod
    def _validate_branch(
        session: Session,
        project_id: UUID,
        branch: str,
    ) -> None:
        """Validate branch before operations."""
        if branch == "main":
            raise ValueError("Cannot operate on main branch")
        # Other validations
```

## Best Practices

1. **Always Use Service Methods**: Don't manipulate branch data directly
2. **Check Permissions**: Verify user has permission before operations
3. **Handle Errors**: Use proper exception handling
4. **Send Notifications**: Notify users of branch operations
5. **Log Operations**: Log all branch operations for audit
6. **Test Thoroughly**: Test all branch operations

## Performance Considerations

### Batch Operations

When merging large branches:
- Process in batches
- Use transactions
- Monitor performance

### Query Optimization

- Use indexes on branch columns
- Limit query scope
- Cache branch data when appropriate

## Security

### Permission Checks

Always check permissions:
```python
if not user.has_permission("merge_branch"):
    raise PermissionError("User cannot merge branches")
```

### Input Validation

Validate all inputs:
```python
if not branch or branch == "":
    raise ValueError("Branch name required")
```
