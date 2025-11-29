# E50004 Soft Delete Pattern Implementation – High-Level Analysis

**Task:** Implement soft delete pattern for all database entities using SQLAlchemy and SQLModel features, updating the base model to support soft deletion across the entire codebase.

**Status:** Analysis Phase
**Date:** 2025-11-23
**Current Time:** 21:04 CET (Europe/Rome)

---

## User Story

As a system administrator, I need all entities to support soft deletion so that deleted records are preserved for audit purposes, data recovery, and historical analysis, while being excluded from normal application queries by default.

---

## 1. Codebase Pattern Analysis

### Existing Model Patterns

1. **SQLModel Base Class Pattern.** All models follow a consistent inheritance structure:
   - `*Base(SQLModel)` - Shared schema fields (no table=True)
   - `*Create(*Base)` - Creation input schema
   - `*Update(SQLModel)` - Update input schema
   - `*(*Base, table=True)` - Database table model with primary key
   - `*Public(*Base)` - API response schema

```91:107:backend/app/models/user.py
class User(UserBase, table=True):
    """User database model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    time_machine_date: date | None = Field(
        default=None, sa_column=Column(Date, nullable=True)
    )
    # Note: openai_base_url and openai_api_key_encrypted are inherited from UserBase
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
```

2. **Timestamp Pattern.** Several models already include `created_at` and `updated_at` fields using `datetime.utcnow` default factory and `DateTime(timezone=True)` columns. This pattern is consistent across User, Project, WBE, CostElement, and others.

3. **Hard Delete Operations.** Current delete endpoints use `session.delete()` followed by `session.commit()`, performing permanent database deletions:

```101:124:backend/app/api/routes/projects.py
@router.delete("/{id}")
def delete_project(
    session: SessionDep, _current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a project.
    """
    project = session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if project has WBEs
    wbes_count = session.exec(
        select(func.count()).select_from(WBE).where(WBE.project_id == id)
    ).one()
    if wbes_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete project with {wbes_count} existing WBE(s). Delete WBEs first.",
        )

    session.delete(project)
    session.commit()
    return Message(message="Project deleted successfully")
```

**Architectural layers to respect:**
- *SQLModel models* in `backend/app/models/` maintain Base/Create/Update/Public/Table model separation
- *FastAPI routers* in `backend/app/api/routes/` handle HTTP contracts and use `SessionDep` for database access
- *Service layer* (e.g., `backend/app/services/`) contains business logic and query helpers
- *Test fixtures* in `backend/tests/` use `conftest.py` for database session management
- *Time-machine filtering* already demonstrates query scoping patterns via `apply_time_machine_filters()` in `backend/app/services/time_machine.py`

---

## 2. Integration Touchpoint Mapping

### Backend Dependencies/Config

- **Base Model Definition**
  - `backend/app/models/` - Need to create a new base mixin class (e.g., `SoftDeleteMixin`) that adds `deleted_at: datetime | None` field
  - All table models (User, Project, WBE, CostElement, etc.) must inherit from this mixin
  - Migration required to add `deleted_at` column to all existing tables

- **Query Filtering**
  - `backend/app/core/db.py` or new `backend/app/core/soft_delete.py` - Implement SQLAlchemy event listeners or query scoping to automatically filter out soft-deleted records
  - All `select()` statements need to exclude `deleted_at IS NOT NULL` by default
  - `session.get()` calls need special handling or wrapper functions

- **Delete Endpoints**
  - `backend/app/api/routes/*.py` - All DELETE endpoints (projects, wbes, users, cost_elements, forecasts, etc.) must be updated to set `deleted_at` instead of calling `session.delete()`
  - Approximately 10+ delete endpoints identified: projects, wbes, users, cost_elements, forecasts, earned_value_entries, cost_registrations, cost_element_schedules, app_configuration, variance_threshold_config

- **Query Helpers**
  - `backend/app/services/time_machine.py` - May need coordination with time-machine filters
  - Service layer queries must respect soft delete filtering
  - Consider helper functions like `get_active_entity()` vs `get_entity_including_deleted()`

- **Database Migrations**
  - Alembic migration to add `deleted_at` column to all tables
  - Index on `deleted_at` for performance (partial index where deleted_at IS NULL for active records)

- **Test Utilities**
  - `backend/tests/conftest.py` - May need to update cleanup logic
  - Test factories may need to support creating soft-deleted entities
  - New test utilities for querying deleted records

### Frontend Touchpoints

- **API Response Handling**
  - No direct changes expected if backend properly filters deleted records
  - Error handling for 404s when accessing deleted entities should remain consistent

- **Configuration**
  - No new configuration required; soft delete behavior should be transparent to frontend

---

## 3. Abstraction Inventory

### Existing Abstractions to Leverage

1. **SQLModel Inheritance.** The Base/Table model pattern allows adding fields to a base mixin that all table models can inherit. SQLModel supports multiple inheritance, enabling a `SoftDeleteMixin` approach.

2. **SQLAlchemy Event Listeners.** SQLAlchemy provides `before_compile` event listeners that can automatically modify queries to exclude soft-deleted records. This can be applied at the engine or session level.

3. **Query Scoping Utilities.** The existing `apply_time_machine_filters()` pattern in `backend/app/services/time_machine.py` demonstrates how to wrap queries with additional filters. A similar pattern could be used for soft delete filtering.

4. **Session Dependency Injection.** `SessionDep` in `backend/app/api/deps.py` provides a centralized place to inject database sessions. Could potentially wrap this to provide a "scoped" session that automatically filters deleted records.

5. **Test Fixtures.** Existing `conftest.py` provides database session fixtures. Can extend these with utilities for testing soft delete behavior.

### Patterns for Implementation

- **Mixin Pattern:** Create `SoftDeleteMixin(SQLModel)` with `deleted_at` field, inherit in all table models
- **Query Filtering:** Use SQLAlchemy `default_filters` or event listeners to automatically add `WHERE deleted_at IS NULL` to queries
- **Delete Method Override:** Create a `soft_delete()` helper method or override `session.delete()` behavior via events
- **Repository Pattern:** Could introduce a repository layer, but this would be a significant architectural change

---

## 4. Alternative Approaches

| Approach | Summary | Pros | Cons/Risks | Architectural Alignment | Complexity |
| --- | --- | --- | --- | --- | --- |
| **A. Mixin + Event Listener (Recommended)** | Create `SoftDeleteMixin` with `deleted_at` field. Use SQLAlchemy `before_compile` event to automatically filter queries. Override delete operations via session events or helper methods. | Minimal code changes per model; automatic query filtering; transparent to most application code; leverages SQLAlchemy features. | Requires understanding SQLAlchemy events; potential edge cases with raw SQL; need to handle `session.get()` specially. | High – uses SQLAlchemy/SQLModel features; respects existing model patterns. | Medium-High (mixin + events + migration + tests). |
| **B. Base Query Class** | Create a custom `SoftDeleteQuery` class and use it for all queries. Manually add `.filter(Model.deleted_at.is_(None))` to every query. | Explicit control; easy to understand; no "magic" behavior. | Requires updating every query in codebase (100+ locations); easy to miss queries; maintenance burden. | Medium – requires extensive refactoring. | High (manual updates everywhere). |
| **C. Repository Pattern** | Introduce repository layer that wraps all database operations and enforces soft delete filtering. | Clean separation; explicit control; easy to test. | Major architectural change; requires refactoring all database access; may conflict with existing patterns. | Low – introduces new architectural layer. | Very High (architectural refactor). |
| **D. Database-Level Views** | Create database views that filter out deleted records, query views instead of tables. | Pushes logic to database; application code unchanged. | Complex migrations; view maintenance; potential performance issues; doesn't work well with SQLModel. | Low – deviates from ORM patterns. | High (database complexity). |
| **E. Hybrid: Mixin + Helper Functions** | Create `SoftDeleteMixin` and provide helper functions like `get_active()`, `soft_delete()`, `restore()`. Manually call helpers in routes/services. | Explicit and clear; no "magic"; easy to opt-in/opt-out. | Requires updating all delete endpoints and queries; easy to forget filtering; more verbose. | Medium – requires discipline. | Medium (systematic updates needed). |

---

## 5. Architectural Impact Assessment

### Principles Upheld

- **Architectural Respect:** Approach A (Mixin + Event Listener) extends existing SQLModel patterns without introducing new architectural layers
- **Incremental Change:** Can be implemented model-by-model if needed, though bulk migration is more efficient
- **Test-Driven Development:** Soft delete behavior can be tested with failing tests before implementation
- **No Code Duplication:** Mixin pattern ensures `deleted_at` field is defined once and reused

### Potential Violations

- **Query Transparency:** Event listeners add "magic" behavior that may not be obvious to developers. Need clear documentation and potentially explicit opt-out mechanisms for queries that need deleted records.
- **Session.get() Behavior:** `session.get()` bypasses query compilation, so event listeners won't apply. Need wrapper functions or special handling.
- **Raw SQL:** Any raw SQL queries will bypass soft delete filtering unless explicitly handled.

### Future Maintenance

- **Documentation:** Must document soft delete behavior in developer guidelines
- **Query Auditing:** Need to ensure all queries respect soft delete (code review process)
- **Migration Strategy:** Existing hard-deleted records will have `deleted_at = NULL` (correct for active records). Need to decide if historical hard deletes should be backfilled.
- **Performance:** Index on `deleted_at` is critical. Partial index `WHERE deleted_at IS NULL` for active records can improve query performance.
- **Cascade Behavior:** Need to decide if soft-deleting a parent (e.g., Project) should soft-delete children (e.g., WBEs). Current hard delete logic checks for children first.

### Testing Challenges

- **Query Filtering Tests:** Need to verify that all query types (select, get, joins, etc.) properly filter deleted records
- **Edge Cases:** Testing `session.get()` behavior, raw SQL, joins with deleted records, foreign key constraints
- **Migration Tests:** Verify migration adds column correctly and doesn't break existing data
- **Restore Functionality:** If restore capability is added, test restore operations
- **Time-Machine Interaction:** Ensure soft delete filtering works correctly with time-machine control date filtering

---

## Risks, Unknowns, and Ambiguities

### Data Semantics

- **Foreign Key Constraints:** How should foreign keys behave with soft-deleted records? Should a Project with `deleted_at IS NOT NULL` still be referenceable by WBEs? Current hard delete logic prevents deletion if children exist.
- **Cascade Behavior:** Should soft-deleting a Project automatically soft-delete all related WBEs, CostElements, etc.? Or should it be prevented (like current hard delete)?
- **Unique Constraints:** If a model has unique constraints (e.g., User.email), should soft-deleted records still enforce uniqueness? Typically yes, but need to confirm business rules.

### Implementation Details

- **`session.get()` Handling:** SQLAlchemy's `session.get()` uses direct primary key lookup and bypasses query compilation, so event listeners won't apply. Need wrapper function or alternative approach.
- **Raw SQL Queries:** Any `session.execute(text("SELECT ..."))` queries will bypass filtering. Need audit and potentially wrapper functions.
- **Join Behavior:** When joining tables, need to ensure both sides respect soft delete filtering.
- **Index Strategy:** Partial index `CREATE INDEX idx_model_deleted_at ON model (deleted_at) WHERE deleted_at IS NULL` for active records vs full index. PostgreSQL supports partial indexes well.

### Migration Strategy

- **Existing Data:** All existing records will have `deleted_at = NULL` (correct for active records)
- **Historical Hard Deletes:** Should we backfill `deleted_at` for records that were previously hard-deleted? Likely not feasible without audit logs.
- **Rollback Plan:** Migration should be reversible in case of issues.

### Performance Considerations

- **Query Performance:** Additional `WHERE deleted_at IS NULL` clause on every query. With proper indexing, impact should be minimal.
- **Index Maintenance:** Partial indexes are efficient but need to be created for each table.
- **Bulk Operations:** Soft-deleting many records (e.g., cleanup jobs) should be efficient.

### Business Rules

- **Restore Capability:** Should users be able to restore soft-deleted records? If yes, need restore endpoints and UI.
- **Permanent Deletion:** Should there be a way to permanently delete (hard delete) soft-deleted records after a retention period?
- **Audit Requirements:** Do audit logs need to track soft delete operations? Current `AuditLog` model may need updates.

---

## Summary & Next Steps

- **What:** Implement soft delete pattern across all database entities by adding `deleted_at` field to base model and automatically filtering deleted records from queries, while updating all delete operations to set `deleted_at` instead of removing records.

- **Why:** Preserves data for audit purposes, enables data recovery, supports historical analysis, and maintains referential integrity while allowing "deletion" from user perspective.

- **Recommended Approach:** Approach A (Mixin + Event Listener) using SQLAlchemy's `before_compile` event to automatically filter queries, with a `SoftDeleteMixin` base class and helper methods for explicit soft delete operations.

- **Next Steps:**
  1. Await feedback on ambiguities (cascade behavior, restore capability, foreign key handling)
  2. Create failing tests for soft delete behavior
  3. Implement `SoftDeleteMixin` base class
  4. Add SQLAlchemy event listeners for query filtering
  5. Create database migration for `deleted_at` columns
  6. Update all delete endpoints to use soft delete
  7. Add helper functions for restore and querying deleted records (if needed)

---

## Decision Log

*To be updated as decisions are made during implementation.*

---

**Pending Confirmation:** Please review and confirm:
1. Should soft-deleting a parent (e.g., Project) prevent deletion if children exist, or should it cascade soft-delete to children?
2. Should there be a restore capability for soft-deleted records?
3. How should foreign key constraints behave with soft-deleted records?
4. Should there be a retention period after which soft-deleted records can be permanently deleted?

Once confirmed, I will proceed with detailed planning and failing tests per our working agreements.
