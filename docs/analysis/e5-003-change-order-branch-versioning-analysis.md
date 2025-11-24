# High-Level Analysis: E5-003 Change Order Branch Versioning Approach

**Task:** E5-003 (Change Order Entry Interface - Git Branch Versioning Approach)
**Status:** Analysis Phase - Decisions Confirmed
**Date:** 2025-11-24
**Current Time:** 05:33 CET (Europe/Rome)
**Analysis Code:** E50003

---

## User Stories

### Primary User Story

**As a** project manager
**I want to** create change orders using a branch-based versioning system where each entity has version, status, and branch attributes
**So that** I can stage changes in isolated branches, merge approved changes into the main branch, and automatically benefit from soft delete and versioning features for all entities.

### Secondary User Stories

**As a** project manager
**I want to** create a change order that automatically creates a branch for staging modifications
**So that** I can work on changes without affecting the main project data until approval.

**As a** project manager
**I want to** modify WBEs, cost elements, and other entities within a change order branch
**So that** I can stage create, update, and delete operations that will be applied only after approval.

**As a** project controller
**I want to** compare the main branch with a change order branch to see all proposed changes
**So that** I can review modifications before approval and understand the full impact.

**As a** project manager
**I want to** merge an approved change order branch into the main branch
**So that** all staged changes are applied to the live project data using last-write-wins conflict resolution.

**As a** project controller
**I want to** see version history for any entity showing all changes over time
**So that** I can track how project elements evolved and audit all modifications.

**As a** system administrator
**I want to** soft delete entities by setting their status to 'deleted' instead of removing them
**So that** deleted records are preserved for audit purposes while being excluded from normal queries.

**As a** project manager
**I want to** work on multiple change orders simultaneously, each in its own branch
**So that** I can handle concurrent scope changes and merge them independently when approved.

**As a** project controller
**I want to** be warned when multiple change orders modify the same entities
**So that** I can review potential merge conflicts before approval.

---

## 1. CODEBASE PATTERN ANALYSIS

### Existing Model Patterns

1. **SQLModel Base Class Pattern.** All models follow a consistent inheritance structure:
   - `*Base(SQLModel)` - Shared schema fields (no table=True)
   - `*Create(*Base)` - Creation input schema
   - `*Update(SQLModel)` - Update input schema
   - `*(*Base, table=True)` - Database table model with primary key
   - `*Public(*Base)` - API response schema

2. **Versioning Pattern (Forecast Model).** The Forecast model demonstrates versioning with `is_current` flag:
   - `is_current: bool = Field(default=False)` - Marks the active version
   - Only one forecast per cost element can have `is_current=True`
   - Versioning logic ensures single current forecast via `ensure_single_current_forecast()` helper

```34:34:backend/app/models/forecast.py
    is_current: bool = Field(default=False)
```

3. **Soft Delete Pattern Analysis.** E50004 analysis document exists for soft delete implementation:
   - Proposed `SoftDeleteMixin` with `deleted_at: datetime | None` field
   - SQLAlchemy event listeners for automatic query filtering
   - Pattern can be adapted for branch-based soft delete via status field

4. **Timestamp Pattern.** Models include `created_at` and `updated_at` fields using `datetime.utcnow` default factory.

**Architectural layers to respect:**
- *SQLModel models* in `backend/app/models/` maintain Base/Create/Update/Public/Table model separation
- *FastAPI routers* in `backend/app/api/routes/` handle HTTP contracts and use `SessionDep` for database access
- *Service layer* (e.g., `backend/app/services/`) contains business logic and query helpers
- *Time-machine filtering* demonstrates query scoping patterns via `apply_time_machine_filters()` in `backend/app/services/time_machine.py`
- *Forecast versioning* demonstrates single-current-version pattern via `ensure_single_current_forecast()` helper

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### Backend Dependencies/Config

**Base Model Extensions:**

**Branch-Enabled Entities (WBE and CostElement only):**
- `backend/app/models/wbe.py` - Add `version: int`, `status: str`, `branch: str` fields
- `backend/app/models/cost_element.py` - Add `version: int`, `status: str`, `branch: str` fields
- Create `BranchVersionMixin(SQLModel)` with `version`, `status`, `branch` fields
- Only WBE and CostElement inherit from BranchVersionMixin (full branching support)

**Version-Only Entities (All other entities):**
- All other entities require `version: int`, `status: str` fields only (no branch field)
- Entities include: Project, User, Forecast, AppConfiguration, VarianceThresholdConfig, ProjectPhase, QualityEvent, ProjectEvent, BudgetAllocation, ChangeOrder, EarnedValueEntry, CostRegistration, CostElementType, CostElementSchedule, Department, BaselineLog, BaselineCostElement, AuditLog
- Create `VersionStatusMixin(SQLModel)` with `version`, `status` fields only
- All other entity models inherit from VersionStatusMixin (versioning and soft delete, no branching)
- These entities always exist in 'main' branch conceptually (branch field not needed)

**Query Filtering:**
- `backend/app/core/db.py` or new `backend/app/core/branch_filtering.py` - Implement query scoping to filter by branch
- **WBE and CostElement queries:** Filter by `branch='main'` and `status='active'` (default) or specific branch
- **All other entity queries:** Filter by `status='active'` only (no branch filtering needed)
- Branch-specific queries for WBE/CostElement: `branch='co-001'` (change order branches)
- Similar pattern to time-machine filtering: `apply_branch_filters()` for WBE/CostElement only

**CRUD Operations:**
- `backend/app/api/routes/wbes.py` - Update all endpoints to support branch parameter
- `backend/app/api/routes/cost_elements.py` - Update all endpoints to support branch parameter
- `backend/app/api/routes/change_orders.py` - New endpoints for branch creation, merging
- **WBE and CostElement:** CREATE/UPDATE operations increment version and set branch
- **All other entities:** CREATE/UPDATE operations increment version only (no branch, always 'main')
- **All entities:** DELETE operations set status='deleted' instead of hard delete (soft delete)

**Branch Management:**
- `backend/app/services/branch_service.py` - New service for branch operations:
  - `create_branch(change_order_id: UUID) -> str` - Creates new branch name
  - `merge_branch(branch: str, change_order_id: UUID)` - Merges branch into main
  - `delete_branch(branch: str)` - Cleans up branch after merge/cancellation
  - `get_branch_elements(branch: str, project_id: UUID)` - Gets all elements in branch

**Version Management:**
- `backend/app/services/version_service.py` - New service for version operations:
  - `get_next_version(entity_type: str, entity_id: UUID, branch: str) -> int` - Gets next version number
  - `get_current_version(entity_type: str, entity_id: UUID, branch: str)` - Gets active version
  - `create_version(entity, branch: str)` - Creates new version in branch

**Database Migrations:**
- **WBE and CostElement tables:** Add `version`, `status`, `branch` columns
  - Default values: `version=1`, `status='active'`, `branch='main'` for existing records
  - Composite index on `(branch, status, entity_id)` for active records
  - Index on `(entity_id, branch, version)` for version lookups
  - Composite unique constraint: `(entity_id, branch, version)` (prevents duplicate versions)
  - Partial index on `(branch, status) WHERE status = 'active'` for active records

- **All other entity tables:** Add `version`, `status` columns only (no branch column)
  - Default values: `version=1`, `status='active'` for existing records
  - Index on `(status, entity_id)` for active records
  - Index on `(entity_id, version)` for version lookups
  - Composite unique constraint: `(entity_id, version)` (prevents duplicate versions)

**Change Order Integration:**
- `backend/app/models/change_order.py` - Add `branch: str` field linking to branch name
- Change order creation automatically creates branch: `branch = f"co-{short_id}"` (e.g., "co-001", "co-002")
- Short ID generation: Extract short identifier from change_order_id or use progressive number
- Change order approval triggers merge operation (last-write-wins strategy)
- Change order cancellation triggers branch soft delete (set status='deleted' for all branch entities)

### Frontend Touchpoints

**API Response Handling:**
- **WBE and CostElement API responses:** Include `branch`, `version`, `status` fields
- **All other entity API responses:** Include `version`, `status` fields only (no branch)
- Frontend must pass `branch` parameter in WBE/CostElement queries (default: 'main')
- Branch selector UI component for switching between branches (WBE/CostElement only)
- Branch comparison view (side-by-side main vs branch for WBE/CostElement)

**UI Components:**
- `frontend/src/components/Projects/BranchSelector.tsx` - Dropdown to select branch
- `frontend/src/components/Projects/BranchComparisonView.tsx` - Side-by-side comparison
- `frontend/src/components/Projects/MergeBranchDialog.tsx` - Merge confirmation dialog
- All WBE/CostElement forms include branch context
- Change order detail view shows branch name and merge status

**Configuration:**
- Default branch: 'main' (hardcoded constant)
- Branch naming convention: `co-{short_id}` (e.g., "co-001", "co-002")
- Short ID: Progressive number based on change order sequence or extracted from UUID

---

## 3. ABSTRACTION INVENTORY

### Existing Abstractions to Leverage

1. **SQLModel Inheritance.** The Base/Table model pattern allows adding fields to a base mixin that all table models can inherit. SQLModel/SQLAlchemy supports mixin inheritance (mixins extending other mixins). Can create:
   - `VersionStatusMixin` with `version`, `status` fields (base mixin for all entities)
   - `BranchVersionMixin(VersionStatusMixin)` with additional `branch` field (extends base mixin for WBE and CostElement)
   - **Best Practice:** Use inheritance pattern to avoid code duplication and follow DRY principle

2. **Query Scoping Utilities.** The existing `apply_time_machine_filters()` pattern in `backend/app/services/time_machine.py` demonstrates how to wrap queries with additional filters. A similar pattern could be used for branch filtering: `apply_branch_filters(query, branch='main')` for WBE/CostElement queries only.

3. **Versioning Pattern (Forecast).** The `ensure_single_current_forecast()` pattern can be adapted for branch-based versioning: `ensure_single_active_version(entity_id, branch)`.

4. **Session Dependency Injection.** `SessionDep` in `backend/app/api/deps.py` provides a centralized place to inject database sessions. Could extend this to provide branch-scoped sessions.

5. **Test Fixtures.** Existing `conftest.py` provides database session fixtures. Can extend these with utilities for testing branch operations.

### Patterns for Implementation

- **Mixin Inheritance Pattern (Recommended):**
  - Create `VersionStatusMixin(SQLModel)` with `version: int`, `status: str` fields (base mixin)
  - Create `BranchVersionMixin(VersionStatusMixin)` extending base mixin with `branch: str` field
  - WBE and CostElement models inherit from `BranchVersionMixin` (gets version, status, branch)
  - All other entity models inherit from `VersionStatusMixin` (gets version, status only)
  - **Benefits:** DRY principle, single source of truth for version/status, clear hierarchy, SQLAlchemy best practice
- **Query Filtering:**
  - WBE/CostElement: Use query scoping to automatically add `WHERE branch = ? AND status = 'active'` to queries
  - All other entities: Use query scoping to automatically add `WHERE status = 'active'` to queries (no branch filtering)
- **Version Increment:** On UPDATE, create new version instead of updating existing (immutable history)
- **Soft Delete:** Set `status='deleted'` instead of hard delete, preserve all versions (all entities)
- **Branch Isolation:** Each branch has independent version sequences (WBE/CostElement only)
- **Merge Operation:** Copy active versions from branch to main for WBE/CostElement, resolve conflicts if needed

---

## 4. ALTERNATIVE APPROACHES

| Approach | Summary | Pros | Cons/Risks | Architectural Alignment | Complexity |
| --- | --- | --- | --- | --- | --- |
| **A. Branch + Version + Status Fields (Recommended)** | Add `version`, `status`, `branch` fields to WBE and CostElement only. Add `version`, `status` fields to all other entities. Main branch is 'main', change orders create branches for WBE/CostElement. CRUD operations work in branches for WBE/CostElement. Merge copies active versions to main. | Automatic soft delete (via status) for all entities; automatic versioning (via version) for all entities; branch isolation for WBE/CostElement; familiar git-like workflow; preserves all history; enables conflict resolution. | Requires adding 3 fields to WBE/CostElement, 2 fields to all other entities; query complexity for WBE/CostElement (filter by branch); merge conflict resolution needed; version number management; more complex queries for WBE/CostElement. | Medium – extends existing model patterns; requires query scoping similar to time-machine for WBE/CostElement only. | High (model changes + query filtering + merge logic + UI). |
| **B. Branch Table + Entity References** | Separate `branch_entity` table that references entities. Entities remain unchanged, branch table tracks which versions exist in which branches. | Entities unchanged; cleaner separation; easier to add to existing system. | More complex joins; harder to query "current state"; requires additional table maintenance; less intuitive. | Low – introduces new table structure. | Very High (new table + complex joins). |
| **C. JSONB Branch Data** | Store branch-specific data in JSONB column. Main data in regular columns, branch modifications in JSONB. | Minimal schema changes; flexible structure. | Complex querying; harder to maintain referential integrity; JSONB performance concerns; less type-safe. | Low – deviates from relational model. | High (JSONB complexity). |

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### Principles Upheld

- **Architectural Respect:** Approach A extends existing SQLModel patterns with mixin inheritance
- **Incremental Change:** Can be implemented entity-by-entity (WBE first, then CostElement)
- **Test-Driven Development:** Branch operations can be tested with failing tests before implementation
- **No Code Duplication:** Mixin pattern ensures branch/version/status fields are defined once and reused

### Potential Violations

- **Query Complexity:** WBE and CostElement queries must filter by branch, adding complexity to these operations. Other entity queries only filter by status.
- **Version Management:** Need to handle version number generation, conflicts, and rollback
- **Merge Complexity:** Merging branches requires conflict detection and resolution logic
- **Performance:** Additional indexes and filters on every query may impact performance
- **Data Volume:** Storing multiple versions increases database size significantly

### Future Maintenance

- **Branch Cleanup:** Need strategy for cleaning up merged/cancelled branches (archive vs delete)
- **Version History:** Long-term storage of all versions may require archival strategy
- **Query Auditing:** Must ensure WBE/CostElement queries respect branch filtering, all entity queries respect status filtering (code review process)
- **Merge Conflicts:** Need clear strategy for handling merge conflicts (manual resolution vs automatic)
- **Performance Monitoring:** Monitor query performance with branch filtering and version lookups

### Testing Challenges

- **Branch Isolation Tests:** Verify that operations in one branch don't affect another
- **Version Increment Tests:** Verify version numbers increment correctly per branch
- **Merge Tests:** Test merge operations, conflict detection, and resolution
- **Query Filtering Tests:** Verify WBE/CostElement queries properly filter by branch, all entity queries properly filter by status
- **Soft Delete Tests:** Verify status='deleted' works correctly with branch filtering
- **Concurrent Operations:** Test concurrent modifications in different branches

---

## Risks, Unknowns, and Ambiguities

### Data Semantics (CONFIRMED)

- **Primary Key Strategy:** ✅ **CONFIRMED** - Keep existing UUID primary key
  - WBE/CostElement: Add composite unique constraint `(entity_id, branch, version)`
  - All other entities: Add composite unique constraint `(entity_id, version)`

- **Foreign Key Constraints:** ✅ **CONFIRMED** - Foreign keys reference `entity_id` only, branch filtering applied at query level for WBE/CostElement

- **Status Values:** ✅ **CONFIRMED** - Enum: `active`, `deleted`, `merged` (extensible) - applies to all entities

- **Version Numbering:** ✅ **CONFIRMED** - Sequential per branch for WBE/CostElement, sequential globally for other entities, start at 1. Version 1 is initial creation.

### Implementation Details (CONFIRMED)

- **Branch Naming:** ✅ **CONFIRMED** - `co-{short-id}` (e.g., "co-001", "co-002"). Short ID is progressive number or extracted from change order identifier.

- **Merge Strategy:** ✅ **CONFIRMED** - Last-write-wins strategy. When merging branch to main, branch versions overwrite main versions for same entities.

- **Version Cleanup:** ✅ **CONFIRMED** - Keep all versions forever for audit trail. No automatic cleanup of versions.

- **Query Performance:** ✅ **CONFIRMED**
  - WBE/CostElement: Composite index on `(branch, status, entity_id)` for active records. Partial index on `(branch, status) WHERE status = 'active'` for PostgreSQL optimization.
  - All other entities: Composite index on `(status, entity_id)` for active records. Index on `(entity_id, version)` for version lookups.

### Business Rules (CONFIRMED)

- **Branch Lifecycle:** ✅ **CONFIRMED** - Branches can be soft deleted (set status='deleted' for all branch entities) after successful merge or change order cancellation. Soft delete preserves history.

- **Concurrent Branches:** ✅ **CONFIRMED** - Yes, multiple change orders can create branches simultaneously and modify same entities. System warns users about concurrent modifications. Merge conflicts resolved using last-write-wins strategy.

- **Main Branch Protection:** ✅ **CONFIRMED** - Users can modify main branch directly (normal operations). Branches are for change orders only. Main branch modifications create new versions in main branch.

---

## Summary & Next Steps

- **What:** Implement branch-based versioning system for change orders where WBE and CostElement have `version`, `status`, and `branch` fields, while all other entities have `version` and `status` fields only. Change orders create branches, CRUD operations happen in branches, approved changes merge into main branch. Automatic soft delete (via status) and versioning (via version) are side benefits for all entities.

- **Why:** Provides git-like workflow for change orders, enables branch isolation for core project structure elements, preserves complete history, and automatically provides soft delete and versioning features for all entities.

- **Recommended Approach:** Approach A (Branch + Version + Status Fields) using **mixin inheritance pattern**:
  - `VersionStatusMixin` as base mixin (version, status) for all entities
  - `BranchVersionMixin(VersionStatusMixin)` as extended mixin (adds branch) for WBE/CostElement only
  - Query scoping for branch filtering (WBE/CostElement only)
  - Merge service for branch integration

- **Mixin Design Decision:** ✅ **Use inheritance pattern** - `BranchVersionMixin` extends `VersionStatusMixin`:
  - **Benefits:** DRY principle, single source of truth, maintainability, type safety, clear hierarchy
  - **SQLAlchemy Best Practice:** Mixin inheritance is well-established and supported
  - **Python MRO:** Method Resolution Order handles inheritance correctly with SQLModel

- **Next Steps:**
  1. ✅ Decisions confirmed (primary key, foreign keys, merge strategy, branch lifecycle)
  2. ✅ Mixin inheritance pattern evaluated and recommended
  3. Create failing tests for branch operations
  4. Implement `VersionStatusMixin` base class (version, status fields)
  5. Implement `BranchVersionMixin(VersionStatusMixin)` extended class (adds branch field)
  6. Add branch filtering to query scoping (WBE/CostElement only)
  7. Create database migration for version/status columns (all entities) and branch column (WBE/CostElement only)
  8. Implement branch service for create/merge/delete operations
  9. Update WBE/CostElement CRUD endpoints to support branch parameter
  10. Update all entity CRUD endpoints to support version/status (soft delete)
  11. Implement merge conflict detection and resolution (last-write-wins)

---

## Decision Log

*To be updated as decisions are made during implementation.*

---

---

## UI EXPERIENCE DESCRIPTION

### Change Order Creation Flow

**Step 1: Create Change Order**
- User clicks "Add Change Order" button in Change Orders tab
- Dialog opens with form fields: Title, Description, Requesting Party, Justification, Effective Date
- User fills form and clicks "Create Change Order"
- **System Action:** Creates change order record and automatically creates branch `co-001` (or next available number)
- **Database:** ChangeOrder record created with `branch='co-001'`, status='design'

**Step 2: Branch Context Indicator**
- Change order detail view shows banner: "Working in branch: co-001"
- Branch selector dropdown shows: "Main" (default) and "co-001" (change order branch)
- User switches to branch "co-001" to start making changes

**Step 3: Modify Entities in Branch**
- User navigates to WBEs or Cost Elements tab
- Branch selector shows "co-001" (current branch)
- User can create, update, or delete entities
- All operations happen in branch "co-001", main branch remains unchanged
- **Database:** New versions created in branch "co-001" with incremented version numbers

**Step 4: Compare Changes**
- User clicks "Compare with Main Branch" button
- Side-by-side comparison view opens:
  - Left panel: Main branch (current production state)
  - Right panel: Branch "co-001" (proposed changes)
- Visual indicators:
  - Green: New entities in branch (not in main)
  - Yellow: Modified entities (different values)
  - Red: Deleted entities (in main, not in branch)
- Financial impact summary shows total budget/revenue changes

**Step 5: Request Approval**
- User clicks "Request Approval" button
- Change order status transitions: design → approve
- Branch "co-001" becomes read-only (locked)
- **Database:** ChangeOrder.status updated to 'approve', branch entities locked

**Step 6: Merge Branch (After Approval)**
- Approver clicks "Approve and Merge" button
- Confirmation dialog: "Merge branch 'co-001' into 'main'? This will apply all changes to production."
- User confirms
- **System Action:** Merges branch using last-write-wins strategy
- **Database:**
  - For each entity in branch "co-001" with status='active':
    - If entity exists in main: Create new version in main with branch values (overwrites)
    - If entity is new: Create version 1 in main branch
    - If entity deleted in branch: Set status='deleted' in main branch
  - Set all branch "co-001" entities status='merged'
  - ChangeOrder.status updated to 'execute'

**Step 7: Branch Cleanup**
- After successful merge, user can soft delete branch
- Click "Archive Branch" button
- **Database:** Set all branch "co-001" entities status='deleted' (soft delete, preserves history)

---

## REAL-WORLD EXAMPLES

### Example 1: Create New WBE in Change Order Branch

**User Perspective:**
1. Project Manager creates change order "Add Assembly Station B" (creates branch "co-003")
2. Switches to branch "co-003" using branch selector
3. Navigates to WBEs tab (shows empty - no WBEs in branch yet)
4. Clicks "Add WBE" button
5. Fills form: Machine Type="Assembly Station B", Revenue=€150,000, Delivery Date=2025-06-30
6. Clicks "Create WBE"
7. WBE appears in list (only visible in branch "co-003")
8. Main branch still shows original WBEs (unchanged)

**Database Changes:**
```sql
-- WBE created in branch "co-003"
INSERT INTO wbe (
    wbe_id, project_id, machine_type, revenue_allocation, delivery_date,
    version, status, branch
) VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    '440e8400-e29b-41d4-a716-446655440000',
    'Assembly Station B',
    150000.00,
    '2025-06-30',
    1,  -- First version in branch
    'active',
    'co-003'
);

-- Main branch unchanged (no WBE with this machine_type exists)
```

**After Merge:**
```sql
-- WBE copied to main branch
INSERT INTO wbe (
    wbe_id, project_id, machine_type, revenue_allocation, delivery_date,
    version, status, branch
) VALUES (
    '660e8400-e29b-41d4-a716-446655440001',  -- New UUID for main branch
    '440e8400-e29b-41d4-a716-446655440000',
    'Assembly Station B',
    150000.00,
    '2025-06-30',
    1,  -- First version in main branch
    'active',
    'main'
);

-- Branch version marked as merged
UPDATE wbe SET status='merged'
WHERE wbe_id='550e8400-e29b-41d4-a716-446655440001' AND branch='co-003';
```

---

### Example 2: Update Cost Element Budget in Branch

**User Perspective:**
1. Project Manager creates change order "Increase Mechanical Engineering Budget" (creates branch "co-004")
2. Switches to branch "co-004"
3. Navigates to Cost Elements tab
4. Sees existing cost element "Mechanical Engineering" (copied from main branch, version 1)
5. Clicks "Edit" on cost element
6. Changes budget from €80,000 to €95,000
7. Clicks "Save"
8. Cost element shows updated budget in branch "co-004"
9. Main branch still shows €80,000 (unchanged)

**Database Changes:**
```sql
-- Original cost element in main branch (unchanged)
SELECT * FROM cost_element
WHERE cost_element_id='440e8400-e29b-41d4-a716-446655440000'
  AND branch='main' AND status='active';
-- Result: budget_bac=80000.00, version=1

-- New version created in branch "co-004"
INSERT INTO cost_element (
    cost_element_id, wbe_id, department_code, budget_bac, revenue_plan,
    version, status, branch
) VALUES (
    '440e8400-e29b-41d4-a716-446655440000',  -- Same entity_id
    '330e8400-e29b-41d4-a716-446655440000',
    'ME',
    95000.00,  -- Updated budget
    108000.00,  -- Updated revenue
    2,  -- New version in branch
    'active',
    'co-004'
);
```

**After Merge (Last-Write-Wins):**
```sql
-- New version created in main branch (overwrites)
INSERT INTO cost_element (
    cost_element_id, wbe_id, department_code, budget_bac, revenue_plan,
    version, status, branch
) VALUES (
    '440e8400-e29b-41d4-a716-446655440000',
    '330e8400-e29b-41d4-a716-446655440000',
    'ME',
    95000.00,  -- Branch value wins
    108000.00,
    2,  -- New version in main (previous version 1 preserved)
    'active',
    'main'
);

-- Previous main version still exists (version 1, status='active' but superseded by version 2)
-- Branch version marked as merged
UPDATE cost_element SET status='merged'
WHERE cost_element_id='440e8400-e29b-41d4-a716-446655440000'
  AND branch='co-004' AND version=2;
```

---

### Example 3: Delete WBE in Branch

**User Perspective:**
1. Project Manager creates change order "Remove Cancelled Machine" (creates branch "co-005")
2. Switches to branch "co-005"
3. Navigates to WBEs tab
4. Sees existing WBE "Assembly Station A" (copied from main branch)
5. Clicks "Delete" on WBE
6. Confirmation dialog: "Delete this WBE? It will be removed when branch is merged."
7. User confirms
8. WBE disappears from branch "co-005" list (soft deleted)
9. Main branch still shows WBE (unchanged)

**Database Changes:**
```sql
-- WBE in main branch (unchanged)
SELECT * FROM wbe
WHERE wbe_id='330e8400-e29b-41d4-a716-446655440001'
  AND branch='main' AND status='active';
-- Result: status='active', version=1

-- WBE soft deleted in branch "co-005"
UPDATE wbe SET status='deleted'
WHERE wbe_id='330e8400-e29b-41d4-a716-446655440001'
  AND branch='co-005' AND version=1;
```

**After Merge:**
```sql
-- WBE soft deleted in main branch
UPDATE wbe SET status='deleted'
WHERE wbe_id='330e8400-e29b-41d4-a716-446655440001'
  AND branch='main' AND status='active';

-- WBE no longer appears in queries (filtered by status='active')
-- But preserved in database for audit trail
```

---

### Example 4: Concurrent Change Orders (Merge Conflict)

**User Perspective:**
1. Project Manager creates change order "CO-006: Increase Budget" (creates branch "co-006")
2. Another Project Manager creates change order "CO-007: Decrease Budget" (creates branch "co-007")
3. Both modify same cost element in their branches:
   - CO-006: Changes budget from €80,000 to €100,000
   - CO-007: Changes budget from €80,000 to €70,000
4. CO-006 is approved and merged first → Main branch budget becomes €100,000
5. When CO-007 is approved and merged:
   - System shows warning: "Conflict detected: Cost Element 'Mechanical Engineering' was modified in main branch since this change order was created. Last-write-wins will apply branch value (€70,000)."
6. User confirms merge
7. Main branch budget becomes €70,000 (CO-007 wins, overwrites CO-006)

**Database Changes:**
```sql
-- After CO-006 merge:
INSERT INTO cost_element (..., budget_bac=100000.00, version=2, branch='main', status='active')
WHERE cost_element_id='440e8400-e29b-41d4-a716-446655440000';

-- After CO-007 merge (last-write-wins):
INSERT INTO cost_element (..., budget_bac=70000.00, version=3, branch='main', status='active')
WHERE cost_element_id='440e8400-e29b-41d4-a716-446655440000';

-- Version history preserved:
-- Version 1: budget_bac=80000.00 (original)
-- Version 2: budget_bac=100000.00 (from CO-006, now superseded)
-- Version 3: budget_bac=70000.00 (from CO-007, current active)
```

---

## DATABASE CHANGES SUMMARY

### Schema Changes

**1. New Mixins (Recommended: Inheritance Pattern)**

**Base Mixin: VersionStatusMixin (All entities):**
```python
class VersionStatusMixin(SQLModel):
    """Base mixin providing version and status fields for all entities."""
    version: int = Field(default=1, nullable=False)
    status: str = Field(default='active', max_length=20, nullable=False)  # Enum: active, deleted, merged
```

**Extended Mixin: BranchVersionMixin (WBE and CostElement only):**
```python
class BranchVersionMixin(VersionStatusMixin):
    """Extended mixin adding branch field for entities that support branching."""
    branch: str = Field(default='main', max_length=50, nullable=False)
```

**Benefits of Inheritance Pattern:**
- ✅ **DRY Principle:** Version and status fields defined once in base mixin
- ✅ **Maintainability:** Changes to version/status logic only need to be made in one place
- ✅ **Type Safety:** BranchVersionMixin automatically includes version and status fields
- ✅ **Clear Hierarchy:** BranchVersionMixin is clearly an extension of VersionStatusMixin
- ✅ **SQLAlchemy Best Practice:** Mixin inheritance is a well-established pattern in SQLAlchemy/SQLModel
- ✅ **Method Resolution Order (MRO):** Python's MRO handles inheritance correctly with SQLModel

**Alternative (Not Recommended): Separate Mixins**
```python
# Separate mixins - duplicates version/status fields
class VersionStatusMixin(SQLModel):
    version: int = Field(default=1, nullable=False)
    status: str = Field(default='active', max_length=20, nullable=False)

class BranchVersionMixin(SQLModel):
    version: int = Field(default=1, nullable=False)  # Duplicated
    status: str = Field(default='active', max_length=20, nullable=False)  # Duplicated
    branch: str = Field(default='main', max_length=50, nullable=False)
```

**2. Entity Models Extended**

**Branch-Enabled Entities (2 entities):**
- `backend/app/models/wbe.py` - Inherit from `BranchVersionMixin` (which extends `VersionStatusMixin`)
- `backend/app/models/cost_element.py` - Inherit from `BranchVersionMixin` (which extends `VersionStatusMixin`)
- **Example:**
  ```python
  class WBE(WBEBase, BranchVersionMixin, table=True):
      wbe_id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
      # Inherits: version, status, branch from BranchVersionMixin
      # BranchVersionMixin inherits version, status from VersionStatusMixin
  ```

**Version-Only Entities (18+ entities):**
- All other entity models inherit from `VersionStatusMixin` directly
- Entities include: Project, User, Forecast, AppConfiguration, VarianceThresholdConfig, ProjectPhase, QualityEvent, ProjectEvent, BudgetAllocation, ChangeOrder, EarnedValueEntry, CostRegistration, CostElementType, CostElementSchedule, Department, BaselineLog, BaselineCostElement, AuditLog
- **Example:**
  ```python
  class Forecast(ForecastBase, VersionStatusMixin, table=True):
      forecast_id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
      # Inherits: version, status from VersionStatusMixin
      # No branch field (always in 'main' conceptually)
  ```

**3. Database Migrations**

**WBE and CostElement tables:**
- Add `version INT NOT NULL DEFAULT 1`
- Add `status VARCHAR(20) NOT NULL DEFAULT 'active'`
- Add `branch VARCHAR(50) NOT NULL DEFAULT 'main'`
- Backfill existing records: `version=1`, `status='active'`, `branch='main'`

**All other entity tables:**
- Add `version INT NOT NULL DEFAULT 1`
- Add `status VARCHAR(20) NOT NULL DEFAULT 'active'`
- Backfill existing records: `version=1`, `status='active'`

**4. Indexes**

**WBE and CostElement:**
- Composite index: `CREATE INDEX idx_wbe_branch_status_id ON wbe (branch, status, wbe_id)`
- Partial index: `CREATE INDEX idx_wbe_active ON wbe (branch, status) WHERE status = 'active'`
- Version lookup index: `CREATE INDEX idx_wbe_version ON wbe (wbe_id, branch, version)`
- Same indexes for CostElement table

**All other entities:**
- Composite index: `CREATE INDEX idx_{entity}_status_id ON {table} (status, {entity_id})`
- Version lookup index: `CREATE INDEX idx_{entity}_version ON {table} ({entity_id}, version)`

**5. Constraints**

**WBE and CostElement:**
- Composite unique constraint: `UNIQUE (wbe_id, branch, version)` on WBE table
- Composite unique constraint: `UNIQUE (cost_element_id, branch, version)` on CostElement table
- Check constraint: `status IN ('active', 'deleted', 'merged')`

**All other entities:**
- Composite unique constraint: `UNIQUE ({entity_id}, version)` on each entity table
- Check constraint: `status IN ('active', 'deleted', 'merged')`

**6. Change Order Model**
- Add `branch: str` field to ChangeOrder model
- Branch naming: `co-{short_id}` (e.g., "co-001", "co-002")

### Query Changes

**Default Query Filtering:**
- **WBE and CostElement queries:** Automatically filter: `WHERE branch = 'main' AND status = 'active'`
- **Branch-specific WBE/CostElement queries:** `WHERE branch = 'co-001' AND status = 'active'`
- **All other entity queries:** Automatically filter: `WHERE status = 'active'` (no branch filtering)
- **Version history queries:**
  - WBE/CostElement: `WHERE {entity_id} = ? AND branch = ? ORDER BY version DESC`
  - Other entities: `WHERE {entity_id} = ? ORDER BY version DESC`

**CRUD Operations:**
- **WBE/CostElement CREATE:** Sets `version=1`, `status='active'`, `branch={current_branch}`
- **Other entities CREATE:** Sets `version=1`, `status='active'` (no branch, always 'main')
- **All entities UPDATE:** Creates new version (increments version, preserves old version)
- **All entities DELETE:** Sets `status='deleted'` (soft delete, preserves record)
- **WBE/CostElement READ:** Filters by `branch` and `status='active'` by default
- **Other entities READ:** Filters by `status='active'` by default (no branch filtering)

**Merge Operation:**
- For each entity in branch with `status='active'`:
  - If exists in main: Create new version in main with branch values (last-write-wins)
  - If new: Create version 1 in main
  - If deleted: Set `status='deleted'` in main
- Set branch entities `status='merged'` after merge

---

**Next Steps:**
1. Create failing tests for branch operations
2. Implement `BranchVersionMixin` base class
3. Add branch filtering to query scoping
4. Create database migration for branch/version/status columns
5. Implement branch service for create/merge/delete operations
6. Update all CRUD endpoints to support branch parameter
7. Implement merge conflict detection and resolution (last-write-wins)
