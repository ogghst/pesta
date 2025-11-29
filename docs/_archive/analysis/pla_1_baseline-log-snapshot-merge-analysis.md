# High-Level Analysis: Baseline Log and Baseline Snapshot Concept Merge

**Task:** PLA-1 - Merge Baseline Log and Baseline Snapshot Concepts
**Status:** Analysis Phase
**Date:** 2025-11-05T16:55:19+01:00
**Current Time:** Wednesday, November 5, 2025, 4:55 PM (Europe/Rome)

---

## Objective

Analyze the current implementation of Baseline Log and Baseline Snapshot to identify opportunities for merging these concepts and functionalities into a unified baseline management system. The goal is to simplify the architecture while maintaining all existing capabilities and ensuring backward compatibility.

---

## Current State Analysis

### Baseline Log Model (`backend/app/models/baseline_log.py`)

**Purpose:** Log entry representing a baseline creation event at a project milestone.

**Fields:**
- `baseline_id` (UUID, PK) - Unique identifier
- `project_id` (UUID, FK → Project) - Project association
- `baseline_type` (STRING) - Type: schedule, earned_value, budget, forecast, combined
- `baseline_date` (DATE) - Date when baseline was created
- `milestone_type` (STRING) - Milestone: kickoff, bom_release, engineering_complete, etc.
- `description` (TEXT, nullable) - Description of baseline
- `is_cancelled` (BOOLEAN) - Soft delete flag
- `created_by_id` (UUID, FK → User) - User who created baseline
- `created_at` (TIMESTAMP) - Creation timestamp

**Relationships:**
- Belongs to Project
- Belongs to User (created_by)
- Has one BaselineSnapshot (via `baseline_id` foreign key in BaselineSnapshot)
- Has many CostElementSchedule (via `baseline_id`)
- Has many EarnedValueEntry (via `baseline_id`)
- Has many BaselineCostElement (via `baseline_id`)

### Baseline Snapshot Model (`backend/app/models/baseline_snapshot.py`)

**Purpose:** Snapshot of project financial state at baseline creation time.

**Fields:**
- `snapshot_id` (UUID, PK) - Unique identifier
- `project_id` (UUID, FK → Project) - Project association
- `baseline_id` (UUID, FK → BaselineLog, nullable) - Link to baseline log
- `baseline_date` (DATE) - Date when snapshot was taken (duplicated from BaselineLog)
- `milestone_type` (STRING) - Milestone type (duplicated from BaselineLog)
- `description` (TEXT, nullable) - Description (duplicated from BaselineLog)
- `department` (STRING, nullable) - Responsible department (NOT in BaselineLog)
- `is_pmb` (BOOLEAN) - Performance Measurement Baseline flag (NOT in BaselineLog)
- `created_by_id` (UUID, FK → User) - User who created snapshot
- `created_at` (TIMESTAMP) - Creation timestamp

**Relationships:**
- Belongs to Project
- Belongs to User (created_by)
- Belongs to BaselineLog (optional, via `baseline_id`)
- Has many BaselineCostElement (via snapshot_id - but currently uses baseline_id)

### Current Relationship Pattern

**One-to-One Relationship:**
- Each BaselineLog has exactly one BaselineSnapshot (created automatically)
- BaselineSnapshot has optional `baseline_id` foreign key
- Snapshot fields duplicate several BaselineLog fields (baseline_date, milestone_type, description)
- Snapshot includes additional fields not in BaselineLog (department, is_pmb)

**Automatic Creation:**
- When BaselineLog is created, `create_baseline_snapshot_for_baseline_log()` automatically:
  1. Creates BaselineSnapshot record with duplicated metadata
  2. Links snapshot to baseline via `baseline_id`
  3. Creates BaselineCostElement records for all cost elements (linked via `baseline_id`, not `snapshot_id`)

### Current API Endpoints

**Baseline Log Endpoints (`/projects/{project_id}/baseline-logs/`):**
- `GET /` - List all baseline logs
- `GET /{baseline_id}` - Get single baseline log
- `POST /` - Create baseline log (auto-creates snapshot)
- `PUT /{baseline_id}` - Update baseline log
- `PUT /{baseline_id}/cancel` - Cancel baseline log
- `GET /{baseline_id}/snapshot` - Get snapshot summary
- `GET /{baseline_id}/cost-elements-by-wbe` - Get cost elements grouped by WBE
- `GET /{baseline_id}/cost-elements` - Get cost elements paginated list

**Observation:** All snapshot-related endpoints are accessed via baseline_id, not snapshot_id.

---

## 1. CODEBASE PATTERN ANALYSIS

### 1.1 Similar Patterns: Auto-Creation with Related Records

**Pattern 1: Cost Element with Budget Allocation (E2-001)**
**Location:** `backend/app/api/routes/cost_elements.py` (lines 153-196)

**Pattern:**
- When CostElement is created, automatically creates BudgetAllocation record
- Uses helper function `create_budget_allocation_for_cost_element()`
- Helper function is separate from route handler
- Transaction integrity maintained with `session.flush()` pattern

**Structure:**
```python
# Route handler
cost_element = CostElement.model_validate(cost_element_in)
session.add(cost_element)
session.flush()  # Get cost_element_id

# Auto-create related record
create_budget_allocation_for_cost_element(
    session=session,
    cost_element=cost_element,
    allocation_type="initial",
    created_by_id=current_user.id,
)

session.commit()
```

**Reusability:**
- ✅ Helper function pattern for auto-creation
- ✅ Transaction integrity with flush/commit
- ✅ Separate concerns (route handler vs. business logic)

**Pattern 2: Cost Element with Schedule (E2-003)**
**Location:** `backend/app/api/routes/cost_elements.py` (implied from E2-003 completion)

**Pattern:**
- When CostElement is created, automatically creates CostElementSchedule
- Similar helper function pattern
- Initial schedule with defaults (start_date=today, end_date=project.completion, progression_type="linear")

**Reusability:**
- ✅ Same pattern as BudgetAllocation
- ✅ Default values for initial creation

### 1.2 Similar Patterns: View Components with Tabs

**Pattern: ViewBaselineSnapshot Component**
**Location:** `frontend/src/components/Projects/ViewBaselineSnapshot.tsx`

**Pattern:**
- Modal dialog with tabbed interface
- Three tabs: Summary, By WBE, All Cost Elements
- Uses Chakra UI Tabs.Root/Tabs.List/Tabs.Content pattern
- State management: `useState` for active tab and modal open state
- Resets to primary tab when modal closes

**Reusability:**
- ✅ Tabbed modal pattern for complex data views
- ✅ State reset on close
- ✅ Consistent with other detail views (ProjectDetail, WBEDetail, CostElementDetail)

**Pattern: Project Detail Tabbed Layout**
**Location:** `frontend/src/routes/_layout/projects.$id.tsx` (lines 342-457)

**Pattern:**
- Tabs.Root with multiple Tabs.Trigger/Tabs.Content pairs
- Tab state managed via URL search params or component state
- Each tab renders different components

**Reusability:**
- ✅ Tabbed layout for parent detail views
- ✅ URL state synchronization pattern (optional)

### 1.3 Similar Patterns: Aggregation Endpoints

**Pattern: Budget Summary Endpoints**
**Location:** `backend/app/api/routes/budget_summary.py`

**Pattern:**
- Project-level aggregation: `/projects/{project_id}/budget-summary/`
- WBE-level aggregation: `/projects/{project_id}/wbes/{wbe_id}/budget-summary/`
- Cost element-level aggregation: `/cost-elements/{cost_element_id}/budget-summary/`
- Returns aggregated values with computed fields (e.g., `cost_percentage_of_budget`)

**Reusability:**
- ✅ Hierarchical aggregation pattern
- ✅ Computed fields in response schemas
- ✅ Consistent endpoint structure

**Pattern: Baseline Snapshot Summary Endpoint**
**Location:** `backend/app/api/routes/baseline_logs.py` (lines 403-504)

**Pattern:**
- Aggregates BaselineCostElement records for a baseline
- Computes totals: total_budget_bac, total_revenue_plan, total_actual_ac, etc.
- Returns `BaselineSnapshotSummaryPublic` schema
- Handles NULL values for optional fields

**Reusability:**
- ✅ Aggregation pattern similar to budget_summary
- ✅ NULL handling for optional fields

### 1.4 Established Architectural Layers

**Backend Architecture:**
- **Router Layer:** `backend/app/api/routes/{resource}.py`
  - Project-scoped routes: `/projects/{project_id}/{resource}/`
  - Standard CRUD: GET (list + detail), POST, PUT, DELETE
  - Uses `SessionDep` and `CurrentUser` dependencies
  - HTTPException for validation (400/404)
  - Returns Public schemas

- **Model Layer:** `backend/app/models/{resource}.py`
  - SQLModel with `table=True` for database models
  - Base/Create/Update/Public schema pattern
  - Relationships via SQLModel `Relationship()`
  - UUID primary keys

- **Helper Functions:**
  - Located in route files or separate utility modules
  - Used for auto-creation logic (e.g., `create_budget_allocation_for_cost_element`)
  - Transaction-safe with flush/commit pattern

**Frontend Architecture:**
- **Component Layer:** `frontend/src/components/Projects/{Component}.tsx`
  - Modal dialogs: DialogRoot/DialogContent pattern
  - Tables: DataTable component with TanStack Table v8
  - Forms: React Hook Form with validation
  - Data fetching: TanStack Query with typed services

- **Service Layer:** Auto-generated from OpenAPI spec
  - `{Resource}Service` classes with typed methods
  - Located in `frontend/src/client/services/`

- **UI Components:** Chakra UI
  - Consistent component library
  - Theme-based styling

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### 2.1 Backend Integration Points

**Files Requiring Modification:**

1. **`backend/app/models/baseline_log.py`**
   - **Current:** BaselineLog model with separate BaselineSnapshot
   - **Change:** Merge BaselineSnapshot fields into BaselineLog
   - **Fields to Add:** `department` (STRING, nullable), `is_pmb` (BOOLEAN, default=False)
   - **Fields to Remove:** None (keep all existing BaselineLog fields)
   - **Migration:** Add new columns to BaselineLog table

2. **`backend/app/models/baseline_snapshot.py`**
   - **Current:** Separate BaselineSnapshot model
   - **Change:** Deprecate or remove BaselineSnapshot model
   - **Alternative:** Keep BaselineSnapshot as read-only view/alias for backward compatibility
   - **Migration:** Data migration from BaselineSnapshot to BaselineLog (if merging)

3. **`backend/app/models/baseline_cost_element.py`**
   - **Current:** BaselineCostElement links to BaselineLog via `baseline_id`
   - **Change:** No change needed (already linked via baseline_id)
   - **Note:** Currently uses `baseline_id`, not `snapshot_id` - this is correct

4. **`backend/app/api/routes/baseline_logs.py`**
   - **Current:** `create_baseline_snapshot_for_baseline_log()` helper creates separate BaselineSnapshot
   - **Change:** Remove snapshot creation logic (or merge into BaselineLog creation)
   - **Endpoints to Update:**
     - `POST /{project_id}/baseline-logs/` - Remove snapshot creation call
     - `GET /{baseline_id}/snapshot` - Return BaselineLog directly (or alias)
     - Other endpoints should work with BaselineLog only

5. **`backend/app/models/cost_element_schedule.py`**
   - **Current:** Links to BaselineLog via `baseline_id`
   - **Change:** No change needed (already correct)

6. **`backend/app/models/earned_value_entry.py`**
   - **Current:** Links to BaselineLog via `baseline_id`
   - **Change:** No change needed (already correct)

### 2.2 Frontend Integration Points

**Files Requiring Modification:**

1. **`frontend/src/components/Projects/BaselineLogsTable.tsx`**
   - **Current:** Displays BaselineLog records with "View" button opening ViewBaselineSnapshot
   - **Change:** View button should open BaselineLog detail view (merged concept)
   - **Impact:** Minimal - table structure unchanged

2. **`frontend/src/components/Projects/ViewBaselineSnapshot.tsx`**
   - **Current:** Modal displaying snapshot data for a BaselineLog
   - **Change:** Rename to `ViewBaseline` or `BaselineDetail` - same functionality
   - **Impact:** Component rename and prop rename (baseline instead of baseline + snapshot)

3. **`frontend/src/components/Projects/BaselineSnapshotSummary.tsx`**
   - **Current:** Displays aggregated snapshot summary
   - **Change:** Rename to `BaselineSummary` - same functionality
   - **Impact:** Component rename, API endpoint may change

4. **`frontend/src/components/Projects/BaselineCostElementsByWBETable.tsx`**
   - **Current:** Displays cost elements grouped by WBE for a baseline
   - **Change:** No change needed - already uses baseline_id

5. **`frontend/src/components/Projects/BaselineCostElementsTable.tsx`**
   - **Current:** Displays paginated cost elements for a baseline
   - **Change:** No change needed - already uses baseline_id

6. **`frontend/src/routes/_layout/projects.$id.tsx`**
   - **Current:** "Baselines" tab renders BaselineLogsTable
   - **Change:** No change needed - table structure unchanged

### 2.3 API Client Integration Points

**Files Requiring Regeneration:**

1. **`frontend/src/client/types.gen.ts`**
   - **Current:** Contains BaselineLogPublic and BaselineSnapshotPublic types
   - **Change:** Regenerate after backend model changes
   - **Impact:** BaselineSnapshotPublic may be removed or deprecated

2. **`frontend/src/client/services/BaselineLogsService.ts`**
   - **Current:** Methods for baseline log CRUD and snapshot endpoints
   - **Change:** Snapshot endpoints may be renamed or removed
   - **Impact:** Service method names may change

### 2.4 System Dependencies

**Database Migrations:**
- Alembic migration to add `department` and `is_pmb` columns to BaselineLog table
- Data migration from BaselineSnapshot to BaselineLog (if merging)
- Optional: Migration to remove BaselineSnapshot table (if deprecating)

**Test Files Requiring Updates:**
- `backend/tests/models/test_baseline_log.py` - Add tests for new fields
- `backend/tests/models/test_baseline_snapshot.py` - May need deprecation or removal
- `backend/tests/api/routes/test_baseline_logs.py` - Update snapshot endpoint tests

---

## 3. ABSTRACTION INVENTORY

### 3.1 Existing Abstractions to Leverage

**Backend Abstractions:**

1. **Helper Function Pattern:**
   - `create_budget_allocation_for_cost_element()` - Auto-creation pattern
   - `create_baseline_snapshot_for_baseline_log()` - Current snapshot creation
   - **Reusable:** Pattern for auto-creating related records
   - **Location:** Route files or utility modules

2. **Validation Functions:**
   - `validate_baseline_type()` - Enum validation
   - `validate_milestone_type()` - Enum validation
   - **Reusable:** Validation pattern for enum fields
   - **Location:** `backend/app/api/routes/baseline_logs.py`

3. **Aggregation Pattern:**
   - Budget summary aggregation logic
   - Baseline snapshot summary aggregation logic
   - **Reusable:** Pattern for computing aggregated totals
   - **Location:** Route files

4. **SQLModel Schema Pattern:**
   - Base/Create/Update/Public schema pattern
   - **Reusable:** Consistent schema structure
   - **Location:** All model files

**Frontend Abstractions:**

1. **DataTable Component:**
   - `@/components/DataTable/DataTable`
   - **Reusable:** Table display with sorting, filtering, pagination
   - **Used by:** BaselineLogsTable, CostElementsTable, etc.

2. **Modal Dialog Pattern:**
   - DialogRoot/DialogContent from Chakra UI
   - **Reusable:** Consistent modal structure
   - **Used by:** ViewBaselineSnapshot, AddBaselineLog, EditBaselineLog, etc.

3. **Tabbed Layout Pattern:**
   - Chakra UI Tabs.Root/Tabs.List/Tabs.Content
   - **Reusable:** Tabbed interfaces for complex views
   - **Used by:** ViewBaselineSnapshot, ProjectDetail, WBEDetail, etc.

4. **Form Validation Hooks:**
   - React Hook Form with validation
   - **Reusable:** Form management pattern
   - **Used by:** All add/edit components

5. **Query Hooks:**
   - TanStack Query with typed services
   - **Reusable:** Data fetching pattern
   - **Used by:** All table and detail components

### 3.2 Dependency Injection Patterns

**Backend:**
- FastAPI dependency injection via `SessionDep` and `CurrentUser`
- No custom DI container - uses FastAPI's built-in system

**Frontend:**
- React Context for theme/global state (Chakra UI)
- TanStack Query for server state management
- No custom DI container

### 3.3 Factory Methods and Utilities

**Backend Test Utilities:**
- `backend/tests/utils/project.py` - `create_random_project()`
- **Reusable:** Test data creation helpers
- **Pattern:** Factory functions for test fixtures

**Frontend Test Utilities:**
- No established test utilities found
- **Opportunity:** Create test utilities for component testing

---

## 4. ALTERNATIVE APPROACHES

### Approach 1: Full Merge - BaselineSnapshot into BaselineLog (Recommended)

**Description:** Merge all BaselineSnapshot fields into BaselineLog model. Remove BaselineSnapshot table entirely. All snapshot functionality becomes part of BaselineLog.

**Implementation:**
- Add `department` and `is_pmb` fields to BaselineLog model
- Remove BaselineSnapshot model and table
- Update all references from BaselineSnapshot to BaselineLog
- Rename API endpoints: `/snapshot` → `/summary` (or keep as alias)
- Update frontend components to use BaselineLog directly

**Pros:**
- ✅ Simplifies architecture - single source of truth
- ✅ Eliminates duplicate fields (baseline_date, milestone_type, description)
- ✅ Reduces database joins (no BaselineSnapshot lookup needed)
- ✅ Clearer mental model - "Baseline" is one concept
- ✅ Easier to maintain - fewer models to manage

**Cons:**
- ❌ Requires data migration from BaselineSnapshot to BaselineLog
- ❌ Breaking change for any external consumers of snapshot endpoints
- ❌ Loss of conceptual separation (log entry vs. snapshot data)
- ❌ Migration complexity if BaselineSnapshot has existing data

**Alignment with Architecture:**
- ✅ Follows single responsibility principle (BaselineLog becomes complete baseline entity)
- ✅ Consistent with other models (CostElement, WBE, Project are self-contained)
- ✅ Matches existing patterns (no separate "snapshot" models elsewhere)

**Estimated Complexity:**
- **Backend:** Medium (6-8 hours)
  - Model update and migration: 2 hours
  - API endpoint updates: 2 hours
  - Test updates: 2 hours
  - Data migration script: 2 hours

- **Frontend:** Low (2-3 hours)
  - Component renames and prop updates: 1 hour
  - API client regeneration: 15 minutes
  - Test updates: 1 hour

**Risk Factors:**
- **Medium Risk:** Data migration if BaselineSnapshot has production data
- **Low Risk:** Breaking API changes if external consumers exist
- **Low Risk:** Frontend component updates (straightforward renames)

### Approach 2: Keep Separate but Make BaselineSnapshot Read-Only View

**Description:** Keep BaselineSnapshot model but make it a read-only view/alias of BaselineLog. BaselineSnapshot becomes a computed/denormalized view for backward compatibility.

**Implementation:**
- Keep BaselineSnapshot model but remove write operations
- BaselineSnapshot automatically created/updated when BaselineLog changes
- API endpoints can use either BaselineLog or BaselineSnapshot (both work)
- Frontend can use either model (maintain backward compatibility)

**Pros:**
- ✅ Backward compatibility - existing code continues to work
- ✅ No breaking changes
- ✅ Gradual migration path

**Cons:**
- ❌ Still maintains duplicate data (baseline_date, milestone_type, description)
- ❌ More complex architecture (two models for same concept)
- ❌ Synchronization overhead (must keep BaselineSnapshot in sync)
- ❌ Confusing mental model (two ways to access same data)

**Alignment with Architecture:**
- ❌ Violates DRY principle (duplicate fields)
- ❌ Inconsistent with other models (no other "view" models)
- ❌ Adds complexity without clear benefit

**Estimated Complexity:**
- **Backend:** Medium-High (8-10 hours)
  - Keep BaselineSnapshot model: 1 hour
  - Create synchronization logic: 3 hours
  - Update API endpoints: 2 hours
  - Test synchronization: 2 hours
  - Documentation: 2 hours

- **Frontend:** Low (1 hour)
  - No changes needed (backward compatible)

**Risk Factors:**
- **Medium Risk:** Synchronization bugs (BaselineSnapshot out of sync)
- **Low Risk:** Maintenance burden (two models to maintain)

### Approach 3: Deprecate BaselineSnapshot Gradually

**Description:** Keep both models but deprecate BaselineSnapshot. Mark BaselineSnapshot as deprecated, add migration path, remove in future release.

**Implementation:**
- Add deprecation warnings to BaselineSnapshot endpoints
- Update documentation to use BaselineLog only
- Provide migration guide for consumers
- Remove BaselineSnapshot in next major version

**Pros:**
- ✅ Backward compatibility during transition
- ✅ Clear deprecation path
- ✅ No immediate breaking changes

**Cons:**
- ❌ Maintains duplicate code during transition period
- ❌ Requires two releases (deprecation + removal)
- ❌ Confusing for new developers (two ways to do same thing)
- ❌ Technical debt until removal

**Alignment with Architecture:**
- ⚠️ Temporary solution - not aligned with clean architecture
- ⚠️ Adds technical debt

**Estimated Complexity:**
- **Backend:** Medium (4-6 hours)
  - Add deprecation warnings: 1 hour
  - Update documentation: 2 hours
  - Plan removal in future: 1 hour

- **Frontend:** Low (1 hour)
  - Update to use BaselineLog: 1 hour

**Risk Factors:**
- **Low Risk:** Technical debt accumulation
- **Low Risk:** Confusion during transition period

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### 5.1 Architectural Principles

**Single Responsibility Principle:**
- **Current:** BaselineLog = event log, BaselineSnapshot = data snapshot
- **After Merge (Approach 1):** BaselineLog = complete baseline entity (log + snapshot)
- **Assessment:** ✅ Merge improves single responsibility (one model for one concept)

**DRY (Don't Repeat Yourself):**
- **Current:** Duplicate fields (baseline_date, milestone_type, description) in both models
- **After Merge:** Fields exist only in BaselineLog
- **Assessment:** ✅ Merge eliminates duplication

**Separation of Concerns:**
- **Current:** BaselineLog creation triggers BaselineSnapshot creation (tight coupling)
- **After Merge:** BaselineLog is self-contained (loose coupling)
- **Assessment:** ✅ Merge improves separation (BaselineLog is independent)

**Consistency:**
- **Current:** Inconsistent with other models (no other "snapshot" models)
- **After Merge:** Consistent with CostElement, WBE, Project (self-contained entities)
- **Assessment:** ✅ Merge improves consistency

### 5.2 Maintenance Burden

**Current State:**
- Two models to maintain (BaselineLog + BaselineSnapshot)
- Synchronization logic required (auto-creation)
- Duplicate fields to keep in sync
- Two API endpoints for same concept (`/baseline-logs/` and `/snapshot`)

**After Merge (Approach 1):**
- Single model to maintain (BaselineLog)
- No synchronization logic needed
- No duplicate fields
- Single API endpoint (`/baseline-logs/`)

**Assessment:** ✅ Merge significantly reduces maintenance burden

### 5.3 Testing Challenges

**Current State:**
- Must test BaselineLog creation + BaselineSnapshot creation together
- Must test synchronization (snapshot matches log)
- Two model test suites to maintain

**After Merge:**
- Single model to test
- No synchronization tests needed
- Simpler test suite

**Assessment:** ✅ Merge simplifies testing

### 5.4 Future Extensibility

**Current State:**
- Adding new baseline fields requires updating two models
- Must maintain synchronization logic
- More complex to extend

**After Merge:**
- Adding new baseline fields requires updating one model
- No synchronization logic to maintain
- Easier to extend

**Assessment:** ✅ Merge improves extensibility

### 5.5 Performance Impact

**Current State:**
- Requires join between BaselineLog and BaselineSnapshot for full data
- Two database queries or one join query

**After Merge:**
- Single table query - no join needed
- Faster queries

**Assessment:** ✅ Merge improves performance (eliminates join)

---

## 6. RISKS AND UNKNOWNS

### 6.1 Known Risks

1. **Data Migration Risk (Medium)**
   - **Risk:** If BaselineSnapshot has production data, migration must preserve all data
   - **Mitigation:** Create comprehensive data migration script with rollback capability
   - **Impact:** Data loss if migration fails

2. **Breaking API Changes (Low)**
   - **Risk:** External consumers may depend on BaselineSnapshot endpoints
   - **Mitigation:** Check for external API consumers, provide migration guide
   - **Impact:** External integrations break if not migrated

3. **Frontend Component Updates (Low)**
   - **Risk:** Component renames and prop changes may introduce bugs
   - **Mitigation:** Comprehensive testing of all baseline-related components
   - **Impact:** UI bugs if components not properly updated

### 6.2 Unknown Factors

1. **Production Data Volume**
   - **Unknown:** How many BaselineSnapshot records exist in production?
   - **Impact:** Affects data migration complexity and time
   - **Action:** Query production database to assess data volume

2. **External API Consumers**
   - **Unknown:** Are there external systems consuming BaselineSnapshot endpoints?
   - **Impact:** Breaking changes affect external integrations
   - **Action:** Check API logs and documentation for external consumers

3. **BaselineSnapshot Usage in Reports**
   - **Unknown:** Are there reports or analytics using BaselineSnapshot directly?
   - **Impact:** Reports may break if BaselineSnapshot is removed
   - **Action:** Search codebase for BaselineSnapshot references

### 6.3 Dependencies

**Upstream Dependencies:**
- BaselineLog creation triggers BaselineSnapshot creation
- CostElementSchedule and EarnedValueEntry link to BaselineLog (not BaselineSnapshot)
- BaselineCostElement links to BaselineLog (not BaselineSnapshot)

**Downstream Dependencies:**
- Frontend components use BaselineSnapshot endpoints
- API client generated from OpenAPI spec includes BaselineSnapshot types

**Assessment:** ✅ Downstream dependencies are manageable (frontend updates required)

---

## 7. RECOMMENDATION

### Recommended Approach: Approach 1 - Full Merge

**Rationale:**
1. **Simplifies Architecture:** Single model for baseline concept (log + snapshot data)
2. **Eliminates Duplication:** Removes duplicate fields and synchronization logic
3. **Improves Performance:** Eliminates database join for snapshot data
4. **Consistent with Codebase:** Matches pattern of other self-contained models
5. **Reduces Maintenance:** Single model to maintain instead of two

**Implementation Strategy:**
1. **Phase 1: Model Update**
   - Add `department` and `is_pmb` fields to BaselineLog
   - Create Alembic migration
   - Update BaselineLog schemas (Base/Create/Update/Public)

2. **Phase 2: Data Migration**
   - Create migration script to copy BaselineSnapshot data to BaselineLog
   - Preserve all BaselineSnapshot records in BaselineLog
   - Validate data integrity

3. **Phase 3: API Updates**
   - Remove `create_baseline_snapshot_for_baseline_log()` helper
   - Update `POST /baseline-logs/` to not create BaselineSnapshot
   - Update `GET /baseline-logs/{baseline_id}/snapshot` to return BaselineLog data
   - Keep endpoint as alias for backward compatibility (or rename to `/summary`)

4. **Phase 4: Frontend Updates**
   - Rename ViewBaselineSnapshot → ViewBaseline
   - Update component props to use BaselineLog only
   - Regenerate API client
   - Update all BaselineSnapshot references

5. **Phase 5: Deprecation (Optional)**
   - Mark BaselineSnapshot model as deprecated
   - Remove BaselineSnapshot table in future release
   - Update documentation

**Estimated Total Effort:**
- Backend: 8-10 hours
- Frontend: 2-3 hours
- Testing: 2-3 hours
- **Total: 12-16 hours**

---

## 8. NEXT STEPS

1. **Clarify with Stakeholders:**
   - Confirm no external API consumers
   - Confirm production data volume
   - Confirm no reports using BaselineSnapshot directly

2. **Proceed to Detailed Planning:**
   - Create detailed implementation plan (TDD approach)
   - Break down into phases with test requirements
   - Define acceptance criteria

3. **Begin Implementation:**
   - Start with Phase 1 (Model Update) following TDD
   - Write failing tests first
   - Implement incrementally

---

**Document Owner:** Development Team
**Review Frequency:** Before implementation begins
