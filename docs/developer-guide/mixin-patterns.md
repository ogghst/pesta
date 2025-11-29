# Mixin Patterns in BackCast

**Last Updated:** November 29, 2025

## Overview

BackCast uses mixin classes to provide reusable functionality across entities. This document explains the mixin pattern and how to use it.

## What are Mixins?

Mixins are base classes that provide specific functionality to other classes through multiple inheritance. In BackCast, mixins provide:

- Version tracking
- Branch support
- Status management
- Common fields and behaviors

## Core Mixins

### VersionStatusMixin

Provides versioning and status tracking for all entities.

```python
from app.models.version_status_mixin import VersionStatusMixin

class Project(ProjectBase, VersionStatusMixin, table=True):
    project_id: UUID = Field(primary_key=True)
    # ... other fields
    # Inherits: entity_id, version, status
```

**Fields Provided:**
- `entity_id: UUID`: Stable identifier across versions
- `version: int`: Sequential version number
- `status: str`: Lifecycle status (active, deleted, merged)

**Usage:**
```python
# Create new version on update
project = update_entity_with_version(
    session=session,
    entity_class=Project,
    entity_id=project.project_id,
    update_data={"project_name": "New Name"},
    entity_type="project",
)
# Creates version 2 with new name
```

### BranchVersionMixin

Extends VersionStatusMixin with branch support for branch-enabled entities.

```python
from app.models.branch_version_mixin import BranchVersionMixin

class WBE(WBEBase, BranchVersionMixin, table=True):
    wbe_id: UUID = Field(primary_key=True)
    # ... other fields
    # Inherits: entity_id, version, status, branch
```

**Fields Provided:**
- All fields from `VersionStatusMixin`
- `branch: str`: Branch name (e.g., 'main', 'co-001')

**Usage:**
```python
# Create WBE in a branch
wbe = WBE(
    wbe_id=uuid.uuid4(),
    project_id=project_id,
    branch="co-001",  # Branch-specific
    entity_id=uuid.uuid4(),
    version=1,
    status="active",
    # ... other fields
)
```

## Using Mixins

### Adding Versioning to an Entity

1. Import the mixin:
```python
from app.models.version_status_mixin import VersionStatusMixin
```

2. Add mixin to class definition:
```python
class MyEntity(MyEntityBase, VersionStatusMixin, table=True):
    my_entity_id: UUID = Field(primary_key=True)
    # ... other fields
```

3. Use versioning functions:
```python
from app.services.entity_versioning import update_entity_with_version

updated = update_entity_with_version(
    session=session,
    entity_class=MyEntity,
    entity_id=entity_id,
    update_data={"field": "value"},
    entity_type="myentity",
)
```

### Adding Branch Support to an Entity

1. Import the branch mixin:
```python
from app.models.branch_version_mixin import BranchVersionMixin
```

2. Add mixin to class definition:
```python
class MyBranchEntity(MyEntityBase, BranchVersionMixin, table=True):
    my_entity_id: UUID = Field(primary_key=True)
    # ... other fields
```

3. Use branch filtering:
```python
from app.services.branch_filtering import apply_branch_filters

statement = select(MyBranchEntity).where(MyBranchEntity.project_id == project_id)
statement = apply_branch_filters(statement, MyBranchEntity, branch="co-001")
entities = session.exec(statement).all()
```

## Mixin Patterns

### Pattern 1: Base Schema + Mixin + Table Model

```python
# Base schema (no table)
class ProjectBase(SQLModel):
    project_name: str
    customer_name: str
    # ... fields

# Table model with mixin
class Project(ProjectBase, VersionStatusMixin, table=True):
    project_id: UUID = Field(primary_key=True)
    # Inherits all fields from ProjectBase and VersionStatusMixin
```

### Pattern 2: Multiple Mixins

```python
class WBE(WBEBase, BranchVersionMixin, table=True):
    # BranchVersionMixin already includes VersionStatusMixin
    # So we get: entity_id, version, status, branch
    wbe_id: UUID = Field(primary_key=True)
```

### Pattern 3: Custom Mixin Behavior

```python
class Project(ProjectBase, VersionStatusMixin, table=True):
    project_id: UUID = Field(primary_key=True)

    # Override mixin behavior if needed
    @property
    def is_active(self) -> bool:
        return self.status == "active"
```

## Best Practices

### 1. Always Use Mixins for Versioning

Don't manually implement versioning:
```python
# ❌ Bad
class Project(SQLModel, table=True):
    version: int
    status: str

# ✅ Good
class Project(ProjectBase, VersionStatusMixin, table=True):
    project_id: UUID = Field(primary_key=True)
```

### 2. Use Appropriate Mixin

Choose the right mixin:
- `VersionStatusMixin`: For entities without branches
- `BranchVersionMixin`: For entities that need branch support

### 3. Don't Override Mixin Fields

Don't redefine mixin fields:
```python
# ❌ Bad
class Project(ProjectBase, VersionStatusMixin, table=True):
    version: int = Field(default=0)  # Don't override

# ✅ Good
class Project(ProjectBase, VersionStatusMixin, table=True):
    # Use mixin's version field as-is
    pass
```

### 4. Use Mixin-Aware Functions

Use functions that understand mixins:
```python
# ✅ Good
from app.services.entity_versioning import update_entity_with_version
updated = update_entity_with_version(...)

# ❌ Bad
project.version += 1
session.add(project)
```

## Common Patterns

### Creating a New Version

```python
from app.services.entity_versioning import update_entity_with_version

updated = update_entity_with_version(
    session=session,
    entity_class=Project,
    entity_id=project_id,
    update_data={"project_name": "New Name"},
    entity_type="project",
)
```

### Soft Deleting

```python
from app.services.entity_versioning import soft_delete_entity

deleted = soft_delete_entity(
    session=session,
    entity_class=Project,
    entity_id=project_id,
    entity_type="project",
)
```

### Restoring

```python
from app.services.entity_versioning import restore_entity

restored = restore_entity(
    session=session,
    entity_class=Project,
    entity_id=project_id,
    entity_type="project",
)
```

### Querying with Branch Filter

```python
from app.services.branch_filtering import apply_branch_filters

statement = select(WBE).where(WBE.project_id == project_id)
statement = apply_branch_filters(statement, WBE, branch="co-001")
wbes = session.exec(statement).all()
```

## Migration Considerations

### Adding Mixin to Existing Entity

1. Create migration to add mixin fields:
```python
def upgrade():
    op.add_column('project', sa.Column('entity_id', UUID))
    op.add_column('project', sa.Column('version', Integer))
    op.add_column('project', sa.Column('status', String(20)))
```

2. Backfill data:
```python
# Set entity_id = primary_key for existing records
# Set version = 1 for existing records
# Set status = 'active' for existing records
```

3. Update model:
```python
class Project(ProjectBase, VersionStatusMixin, table=True):
    # Now includes mixin fields
```

## Troubleshooting

### Mixin Fields Not Appearing

- Ensure mixin is in class definition
- Check that `table=True` is set
- Verify mixin is imported correctly

### Version Not Incrementing

- Use `update_entity_with_version()` instead of direct updates
- Check that `VersionService.get_next_version()` is called
- Verify entity_type is correct

### Branch Filter Not Working

- Ensure entity uses `BranchVersionMixin`
- Check that `apply_branch_filters()` is called
- Verify branch context is set correctly
