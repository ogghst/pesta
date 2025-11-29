# Branch Versioning Architecture

**Last Updated:** November 29, 2025

## Overview

The branch versioning system in BackCast enables isolated work on change orders through a branch-based architecture. This document describes the technical architecture, design decisions, and implementation details.

## Core Concepts

### Entity Versioning

All entities in BackCast support versioning through the `VersionStatusMixin`:

```python
class VersionStatusMixin(SQLModel):
    entity_id: UUID  # Stable identifier across versions
    version: int      # Sequential version number
    status: str      # Lifecycle status (active, deleted, merged)
```

### Branch Versioning

Branch-enabled entities (WBE, CostElement) extend versioning with branch support through `BranchVersionMixin`:

```python
class BranchVersionMixin(VersionStatusMixin):
    branch: str  # Branch name (e.g., 'main', 'co-001')
```

### Branch Context

Branch filtering is handled through a context variable system:

```python
from app.services.branch_filtering import set_branch_context, get_branch_context

# Set branch context
set_branch_context("co-001")

# Get current branch
current_branch = get_branch_context()  # Returns "co-001"
```

## Architecture Components

### 1. Mixin Classes

#### VersionStatusMixin

Base mixin providing versioning for all entities:
- `entity_id`: Stable identifier shared across versions
- `version`: Sequential version number
- `status`: Lifecycle state

#### BranchVersionMixin

Extends VersionStatusMixin with branch support:
- Adds `branch` field
- Enables branch-specific queries
- Supports branch filtering

### 2. Services

#### BranchService

Handles branch operations:
- `create_branch()`: Creates a new branch for a change order
- `merge_branch()`: Merges branch changes into main
- `delete_branch()`: Soft-deletes a branch
- `clone_branch()`: Creates a copy of a branch
- `lock_branch()`: Locks a branch from modifications

#### VersionService

Manages version numbers:
- `get_next_version()`: Gets the next version number for an entity
- `get_version_history()`: Retrieves version history for an entity

#### EntityVersioningService

Core versioning operations:
- `update_entity_with_version()`: Creates a new version on update
- `soft_delete_entity()`: Soft-deletes by creating deleted version
- `restore_entity()`: Restores a soft-deleted entity
- `hard_delete_entity()`: Permanently deletes an entity

### 3. Query Filtering

#### Branch Filtering

Automatically filters queries by branch and status:

```python
from app.services.branch_filtering import apply_branch_filters

statement = select(WBE).where(WBE.project_id == project_id)
statement = apply_branch_filters(statement, WBE, branch="co-001")
wbes = session.exec(statement).all()  # Only WBEs in co-001 branch
```

#### Status Filtering

Filters queries by entity status:

```python
from app.services.branch_filtering import apply_status_filters

statement = select(Project).where(Project.project_id == project_id)
statement = apply_status_filters(statement, Project)
projects = session.exec(statement).all()  # Only active projects
```

### 4. API Layer

#### Branch Endpoints

- `POST /api/v1/branches`: Create a branch
- `POST /api/v1/branches/{branch}/merge`: Merge a branch
- `DELETE /api/v1/branches/{branch}`: Delete a branch
- `POST /api/v1/branches/{branch}/clone`: Clone a branch
- `POST /api/v1/branches/{branch}/lock`: Lock a branch
- `POST /api/v1/branches/{branch}/unlock`: Unlock a branch

#### Change Order Endpoints

- `GET /api/v1/projects/{project_id}/change-orders`: List change orders
- `POST /api/v1/projects/{project_id}/change-orders`: Create change order
- `GET /api/v1/change-orders/{change_order_id}`: Get change order
- `PUT /api/v1/change-orders/{change_order_id}`: Update change order
- `DELETE /api/v1/change-orders/{change_order_id}`: Delete change order

## Data Flow

### Creating a Change Order

1. User creates change order via API
2. `ChangeOrderService.create_change_order()` is called
3. Change order entity is created with status="active"
4. `BranchService.create_branch()` creates a new branch
5. Branch name is assigned to change order
6. Response includes branch information

### Making Changes in a Branch

1. User selects branch via branch selector
2. Branch context is set via `set_branch_context()`
3. User makes modifications (e.g., updates WBE)
4. `update_entity_with_version()` creates new version in branch
5. Query filters automatically apply branch filter
6. Only branch data is returned

### Merging a Branch

1. User initiates merge via API
2. `BranchService.merge_branch()` is called
3. Branch comparison identifies changes:
   - Creates: New entities in branch
   - Updates: Modified entities
   - Deletes: Soft-deleted entities
4. Conflicts are detected and resolved
5. Changes are applied to main branch:
   - Creates: New entities created in main
   - Updates: New versions created in main
   - Deletes: Entities soft-deleted in main
6. Branch is soft-deleted
7. Notifications are sent

## Design Decisions

### Why Mixins?

Mixins provide:
- **Reusability**: Same versioning logic across all entities
- **Flexibility**: Entities can opt into versioning
- **Consistency**: Uniform versioning behavior
- **Maintainability**: Single source of truth for versioning

### Why Context Variables?

Context variables enable:
- **Thread-safe**: Each request has its own context
- **Automatic**: Filters apply automatically
- **Transparent**: No need to pass branch everywhere
- **Flexible**: Can be overridden when needed

### Why Soft Delete?

Soft delete provides:
- **Recovery**: Can restore deleted items
- **History**: Preserves audit trail
- **Safety**: Prevents accidental data loss
- **Compliance**: Meets data retention requirements

### Why Branch-Based?

Branch-based approach enables:
- **Isolation**: Changes don't affect main until merged
- **Collaboration**: Multiple changes can be worked on simultaneously
- **Review**: Changes can be reviewed before merging
- **Rollback**: Can discard branch without affecting main

## Database Schema

### Change Order Table

```sql
CREATE TABLE changeorder (
    change_order_id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    branch VARCHAR(50),
    entity_id UUID NOT NULL,
    version INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    -- ... other fields
);
```

### Branch-Enabled Tables

Tables with `BranchVersionMixin` include:
- `branch VARCHAR(50)`: Branch name
- `entity_id UUID`: Stable identifier
- `version INT`: Version number
- `status VARCHAR(20)`: Status

## Performance Considerations

### Indexing

Key indexes for performance:
- `(entity_id, branch, version)`: Fast version lookups
- `(branch, status)`: Fast branch filtering
- `(project_id, branch)`: Fast project-branch queries

### Query Optimization

- Use `apply_branch_filters()` for automatic optimization
- Leverage database indexes
- Batch operations when possible
- Cache branch context when appropriate

## Security

### Permissions

Branch operations require:
- **Read**: View branch data
- **Write**: Modify branch data
- **Merge**: Merge branch into main
- **Admin**: Full branch control

### Validation

- Branch names are validated
- Merge operations are validated
- Permissions are checked
- Conflicts are detected

## Testing

### Unit Tests

Test individual components:
- Mixin behavior
- Service methods
- Query filtering
- API endpoints

### Integration Tests

Test complete flows:
- Change order creation
- Branch operations
- Merge operations
- Version history

### E2E Tests

Test user workflows:
- Create change order
- Make changes in branch
- Merge branch
- View version history

## Future Enhancements

Potential improvements:
- Branch templates
- Branch permissions
- Branch notifications
- Branch analytics
- Branch archival
- Branch comparison UI
