# High-Level Analysis: E3-005 Baseline Log Implementation

**Task:** E3-005 - Baseline Log Implementation
**Sprint:** Sprint 3 - Cost Registration and Data Entry
**Status:** Analysis Phase - Clarifications Received
**Date:** 2025-11-04T12:58:21+01:00
**Last Updated:** 2025-11-04 (stakeholder clarifications received)

---

## Objective

Build a baseline tracking system for schedule and earned value baselines. The Baseline Log will replace boolean flags with proper `baseline_id` references, enabling proper baseline management, historical comparison, and trend analysis. This is a prerequisite for E3-007 (Earned Value Baseline Management) and E4-001 (Planned Value Calculation Engine).

---

## Requirements Summary

**From PRD (Section 10.1 - 10.3):**
- System shall support creation of cost and schedule baselines at significant project milestones
- Baseline events must capture: baseline date, event description, event classification (milestone type), responsible department
- System shall maintain all historical baselines for comparison
- Performance Measurement Baseline (PMB) must be trackable
- Baseline Log shall maintain complete event history (no deletion)

**From Data Model (Section 14):**
- Baseline Log maintains a log of all baseline creation events
- Each baseline identified by unique `baseline_id`
- Can be associated with schedule baselines, earned value baselines, or other baseline types
- Attributes: `baseline_id` (UUID, PK), `baseline_type` (ENUM: schedule, earned_value, budget, forecast, combined), `baseline_date` (DATE), `milestone_type` (ENUM), `description` (TEXT, NULL), `is_cancelled` (BOOLEAN), `created_by` (UUID, FK → User), `created_at` (TIMESTAMP), `project_id` (UUID, FK → Project)
- Relationships: Has many Cost Element Schedules (schedule baselines), Has many Earned Value Entries (earned value baselines), Belongs to Project
- **Snapshotting:** When a baseline is created, automatically snapshot budget/cost/revenue data for all cost elements in the project

**Stakeholder Clarifications (2025-11-04):**
- **Snapshotting:** Performed automatically when baselining - it's the same operation and includes automatic snapshotting of budget/cost/revenues
- **Deletion:** A baseline can be soft deleted by marking as cancelled (add `is_cancelled` field)
- **Milestone Types:** Add `milestone_type` field to BaselineLog (ENUM: kickoff, bom_release, engineering_complete, procurement_complete, manufacturing_start, shipment, site_arrival, commissioning_start, commissioning_complete, closeout)
- **UI Placement:** Place UI in a specific tab in the project detail page

**From Project Status:**
- E3-005 is required for proper baseline management
- Replaces boolean flags with baseline_id references
- CostElementSchedule and EarnedValueEntry already have `baseline_id` field (nullable) - ready to link
- E3-007 depends on this (Earned Value Baseline Management)

**From Plan.md (Sprint 3):**
- Baseline Log Implementation is a Sprint 3 deliverable
- Required for baseline management at project milestones

---

## 1. CODEBASE PATTERN ANALYSIS

### 1.1 Existing Baseline Log Model

**Location:** `backend/app/models/baseline_log.py`

**Current State:**
- ✅ Model exists with all required fields: `baseline_id`, `baseline_type`, `baseline_date`, `description`, `created_by_id`, `created_at`
- ✅ Base/Create/Update/Public schema pattern implemented
- ✅ Relationship to User via `created_by_id`
- ✅ Tests exist: `backend/tests/models/test_baseline_log.py` (4 tests passing)
- ❌ **Missing:** `project_id` foreign key (should belong to Project per data model)
- ❌ **Missing:** `milestone_type` field (ENUM for standard milestones)
- ❌ **Missing:** `is_cancelled` field (for soft delete functionality)
- ❌ **Missing:** API routes for CRUD operations
- ❌ **Missing:** Automatic snapshotting logic on baseline creation
- ❌ **Missing:** Frontend components

**Schema Structure (Current):**
```python
BaselineLogBase → baseline_type, baseline_date, description
BaselineLogCreate → + created_by_id
BaselineLogUpdate → baseline_type?, baseline_date?, description?
BaselineLog → baseline_id (PK), created_by_id (FK), created_at
BaselineLogPublic → baseline_id, created_by_id, created_at
```

**Schema Structure (Required After Update):**
```python
BaselineLogBase → baseline_type, baseline_date, milestone_type, description, is_cancelled
BaselineLogCreate → + project_id, created_by_id
BaselineLogUpdate → baseline_type?, baseline_date?, milestone_type?, description?, is_cancelled?
BaselineLog → baseline_id (PK), project_id (FK), created_by_id (FK), is_cancelled (default=False), created_at
BaselineLogPublic → baseline_id, project_id, created_by_id, is_cancelled, created_at
```

### 1.2 Related Models Already Prepared

**CostElementSchedule (`backend/app/models/cost_element_schedule.py`):**
- ✅ Has `baseline_id: uuid.UUID | None` field (nullable foreign key)
- ✅ Has `baseline_log: BaselineLog | None` relationship
- ✅ Ready to link schedules to Baseline Log entries

**EarnedValueEntry (`backend/app/models/earned_value_entry.py`):**
- ✅ Has `baseline_id: uuid.UUID | None` field (nullable foreign key)
- ✅ Has `baseline_log: BaselineLog | None` relationship
- ✅ Ready to link earned value entries to Baseline Log entries

**Observation:** The foreign key infrastructure is already in place. We need to:
1. Add `project_id` to BaselineLog model (migration required)
2. Create CRUD API endpoints
3. Create frontend components for baseline management

### 1.3 Established Architectural Layers

**Backend Architecture:**
- **Router Layer:** `backend/app/api/routes/{resource}.py`
  - Standard CRUD endpoints: GET (list + detail), POST, PUT, DELETE
  - Uses `SessionDep` and `CurrentUser` dependencies
  - HTTPException for validation errors (400/404)
  - Returns Public schemas in responses
- **Model Layer:** `backend/app/models/{resource}.py`
  - SQLModel with `table=True` for database models
  - Base/Create/Update/Public schema pattern
  - Relationships via SQLModel `Relationship()`
  - UUID primary keys throughout
- **Test Pattern:** `backend/tests/api/routes/test_{resource}.py`
  - Comprehensive test coverage (121+ tests passing)
  - Test fixtures in `backend/tests/utils/`
  - Validates both success and error cases

**Frontend Architecture:**
- **Component Layer:** `frontend/src/components/Projects/{Component}.tsx`
  - Modal dialog pattern (DialogRoot/DialogContent)
  - React Hook Form for form management
  - TanStack Query for data fetching and mutations
  - Custom hooks for reusable logic
- **Service Layer:** Auto-generated from OpenAPI spec
  - `{Resource}Service` classes with typed methods
  - Located in `frontend/src/client/services/`
- **UI Components:** Chakra UI components
  - Field, Input, Textarea, Select for form inputs
  - Dialog, Button, Text for layout
  - Toast notifications via `useCustomToast`

### 1.4 Reference Implementation Patterns

**Pattern 1: Cost Element Schedule CRUD (E2-003)**
**Location:** `backend/app/api/routes/cost_element_schedules.py`

**Pattern:**
- `GET /cost-element-schedules/?cost_element_id={id}` - Get by cost element
- `POST /cost-element-schedules/?cost_element_id={id}` - Create with query param
- `PUT /cost-element-schedules/{id}` - Update by ID
- `DELETE /cost-element-schedules/{id}` - Delete by ID
- Validation: Check cost element exists, validate dates
- Returns `CostElementSchedulePublic` schema

**Reusable Components:**
- Query parameter pattern for parent resource (`cost_element_id`)
- Validation function pattern (`validate_cost_element_exists`)
- Date validation pattern (end_date >= start_date)
- Error handling with HTTPException

**Pattern 2: Project-Scoped Endpoints (Budget Summary)**
**Location:** `backend/app/api/routes/budget_summary.py`

**Pattern:**
- `GET /budget-summary/project/{project_id}` - Project-level aggregation
- `GET /budget-summary/wbe/{wbe_id}` - WBE-level aggregation
- Validates project/WBE exists before processing
- Returns summary schemas with computed fields

**Reusable Components:**
- Project-scoped endpoint pattern (`/resource/{resource_id}`)
- Validation pattern: `project = session.get(Project, project_id); if not project: raise HTTPException(404)`
- Hierarchical query pattern for nested resources

**Pattern 3: Cost Registration CRUD (E3-001)**
**Location:** `backend/app/api/routes/cost_registrations.py`

**Pattern:**
- Full CRUD with filtering by `cost_element_id`
- `GET /cost-registrations/` with query params
- `GET /cost-registrations/{id}` for detail
- `POST /cost-registrations/` with validation
- `PUT /cost-registrations/{id}` for updates
- `DELETE /cost-registrations/{id}` for deletion
- Validation helpers for cost element and category

**Reusable Components:**
- List endpoint with filtering pattern
- Validation helper functions
- Error handling patterns

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### 2.1 Files to Create

1. **`backend/app/api/routes/baseline_logs.py`** (new)
   - CRUD API endpoints for Baseline Log
   - Endpoints:
     - `GET /api/v1/projects/{project_id}/baseline-logs/` - List all baselines for a project (filter out cancelled if needed)
     - `GET /api/v1/projects/{project_id}/baseline-logs/{id}` - Get single baseline
     - `POST /api/v1/projects/{project_id}/baseline-logs/` - Create new baseline (with automatic snapshotting)
     - `PUT /api/v1/projects/{project_id}/baseline-logs/{id}` - Update baseline
     - `PUT /api/v1/projects/{project_id}/baseline-logs/{id}/cancel` - Cancel baseline (soft delete by setting is_cancelled=True)
   - Validation: Check project exists, validate baseline_type enum, validate milestone_type enum
   - **Automatic Snapshotting:** On POST, automatically create BaselineSnapshot and BaselineCostElement records for all cost elements
   - Returns `BaselineLogPublic` schema

2. **`backend/tests/api/routes/test_baseline_logs.py`** (new)
   - Test cases for all CRUD operations
   - Test project-scoped listing
   - Test validation (project not found, invalid baseline_type, invalid milestone_type)
   - Test automatic snapshotting on baseline creation
   - Test soft delete (cancel baseline)
   - Test relationships (linking to schedules and earned value entries)

3. **`backend/alembic/versions/XXXX_add_project_id_to_baseline_log.py`** (new migration)
   - Add `project_id` column to `baselinelog` table
   - Add `milestone_type` column (STRING, max_length=100)
   - Add `is_cancelled` column (BOOLEAN, default=False)
   - Add foreign key constraint to `project.project_id`
   - Add index on `project_id` for query performance
   - Add index on `is_cancelled` for filtering cancelled baselines

4. **Frontend Components (to be created in detailed plan):**
   - `frontend/src/components/Projects/BaselineLogsTable.tsx` - List baselines (with cancelled filter)
   - `frontend/src/components/Projects/AddBaselineLog.tsx` - Create baseline modal (with milestone_type dropdown)
   - `frontend/src/components/Projects/EditBaselineLog.tsx` - Edit baseline modal
   - `frontend/src/components/Projects/CancelBaselineLog.tsx` - Cancel baseline confirmation
   - Integration into project detail page as dedicated tab

### 2.2 Files to Modify

1. **`backend/app/models/baseline_log.py`**
   - Add `project_id: uuid.UUID` field to `BaselineLog` model
   - Add `milestone_type: str` field (ENUM: kickoff, bom_release, engineering_complete, procurement_complete, manufacturing_start, shipment, site_arrival, commissioning_start, commissioning_complete, closeout)
   - Add `is_cancelled: bool` field (default=False) for soft delete
   - Add `project: Project | None` relationship
   - Update `BaselineLogCreate` to include `project_id`
   - Update `BaselineLogPublic` to include `project_id`, `milestone_type`, `is_cancelled`
   - Add foreign key constraint: `Field(foreign_key="project.project_id", nullable=False)`

2. **`backend/app/models/__init__.py`**
   - Already exports BaselineLog models (no change needed unless new schemas added)

3. **`backend/app/api/main.py`**
   - Register new `baseline_logs` router
   - Pattern: `api_router.include_router(baseline_logs.router)`

4. **`frontend/src/routes/_layout/projects.$id.tsx`** (project detail page)
   - Add dedicated "Baselines" tab to existing tabbed layout
   - Integrate BaselineLogsTable component in tab
   - Add "Create Baseline" button in tab header
   - Follow existing tab pattern (Info, WBEs, Cost Elements, etc.)

5. **Frontend Client Generation (automatic)**
   - `frontend/src/client/sdk.gen.ts` - Will be regenerated after API changes
   - `frontend/src/client/schemas.gen.ts` - Will be regenerated with updated schemas

### 2.3 Database Schema Changes

**Migration Required:**
```python
# Add project_id to BaselineLog table
alter_table('baselinelog')
    .add_column(Column('project_id', UUID, ForeignKey('project.project_id'), nullable=False))
    .create_index('ix_baselinelog_project_id', 'project_id')
```

**Data Migration:**
- Existing BaselineLog records (if any) will need `project_id` populated
- Existing records will need `milestone_type` set to default value or NULL
- Existing records will have `is_cancelled=False` by default
- May need to handle NULL `project_id` during migration if data exists

**Snapshotting Logic:**
- On baseline creation, automatically create BaselineSnapshot record
- Create BaselineCostElement records for each cost element in the project
- Snapshot: budget_bac, revenue_plan, actual_ac (from cost registrations), forecast_eac (if exists), earned_ev (if exists)

### 2.4 System Dependencies

- **Database:** SQLModel/SQLAlchemy for queries and migrations
- **Authentication:** `CurrentUser` dependency from `app.api.deps`
- **Session Management:** `SessionDep` dependency from `app.api.deps`
- **Models:** `BaselineLog`, `Project`, `User` from `app.models`
- **Migration Tool:** Alembic for schema changes

### 2.5 Configuration Patterns

- Router prefix: `/projects/{project_id}/baseline-logs` (project-scoped)
- Tags: `["baseline-logs"]` for API documentation grouping
- No additional configuration needed - uses existing database connection and authentication patterns

---

## 3. ABSTRACTION INVENTORY

### 3.1 Reusable Abstractions

1. **Validation Helper Functions** (from `cost_elements.py`, `cost_registrations.py`):
   - `validate_project_exists()` - Can be reused for project validation
   - Pattern: `project = session.get(Project, project_id); if not project: raise HTTPException(404)`
   - Error handling with HTTPException

2. **Query Pattern** (from `budget_summary.py`, `cost_registrations.py`):
   - Project-scoped query pattern: `select(BaselineLog).where(BaselineLog.project_id == project_id)`
   - List endpoint with filtering pattern
   - Pagination pattern (skip, limit) if needed

3. **Response Schema Pattern** (from existing models):
   - `BaselineLogPublic` already exists - just needs `project_id` added
   - List response pattern: `BaselineLogsPublic` with `data: list[BaselineLogPublic]` and `count: int`

4. **Test Utilities** (from existing test files):
   - Project creation patterns from `test_projects.py`
   - User creation patterns from `test_baseline_log.py`
   - Test structure: setup → call endpoint → assert structure → assert values

5. **Frontend Component Patterns** (from existing components):
   - `AddProject.tsx`, `AddWBE.tsx`, `AddCostElement.tsx` - Modal form patterns
   - `EditCostElement.tsx` - Edit form patterns
   - DataTable component for list views
   - React Hook Form integration patterns

### 3.2 Dependency Injection Patterns

- **SessionDep:** Standard FastAPI dependency for database session
- **CurrentUser:** Standard dependency for authentication (already used throughout)
- No custom dependencies needed

### 3.3 Test Utilities Available

- `tests/utils/` - Standard test utilities for creating test data
- Test client and fixtures from `conftest.py`
- Project/WBE/CostElement creation helpers from existing tests

---

## 4. ALTERNATIVE APPROACHES

### Approach 1: Project-Scoped CRUD API (RECOMMENDED)

**Description:** Create project-scoped endpoints following the pattern from `budget_summary.py`. All baseline log operations are scoped to a project via URL path.

**Pros:**
- ✅ Follows established project-scoped pattern (budget_summary, budget_timeline)
- ✅ Clear API hierarchy: `/projects/{project_id}/baseline-logs/`
- ✅ Natural fit for PRD requirement (baselines belong to projects)
- ✅ Easy to validate project exists before operations
- ✅ Consistent with existing architecture
- ✅ Supports future filtering by project
- ✅ Clear separation of concerns

**Cons:**
- ⚠️ Slightly longer URL paths
- ⚠️ Requires project_id in all operations

**Estimated Complexity:** Low-Medium
- Backend: 3-4 hours (CRUD endpoints + tests)
- Migration: 1 hour
- Frontend: 4-5 hours (components + integration)
- **Total: 8-10 hours**

**Risk Factors:**
- Low risk - follows established patterns
- Migration needs careful handling of existing data

---

### Approach 2: Independent Resource with Project Filtering

**Description:** Create standalone `/baseline-logs/` endpoints with `project_id` as a query parameter or required field.

**Pros:**
- ✅ Simpler URL structure
- ✅ More flexible for future cross-project queries
- ✅ Follows RESTful resource pattern

**Cons:**
- ❌ Doesn't match existing project-scoped patterns
- ❌ Requires project_id in request body (POST) or query params (GET)
- ❌ Less intuitive API design
- ❌ Inconsistent with existing architecture

**Estimated Complexity:** Medium
- Similar effort to Approach 1, but creates architectural inconsistency

**Risk Factors:**
- Medium risk - creates inconsistency with existing patterns

---

### Approach 3: Hybrid Approach (List Project-Scoped, Detail Independent)

**Description:** List endpoints scoped to project (`/projects/{project_id}/baseline-logs/`), but detail/update/delete use independent IDs (`/baseline-logs/{id}`).

**Pros:**
- ✅ Flexible for detail operations
- ✅ Project-scoped listing for natural filtering

**Cons:**
- ❌ Inconsistent URL patterns
- ❌ More complex routing
- ❌ Requires validation of project_id matches in detail operations

**Estimated Complexity:** Medium-High
- More complex validation logic
- Inconsistent patterns

**Risk Factors:**
- Medium risk - inconsistent patterns may confuse users

---

### Approach 4: Baseline Log as Embedded Resource (No Direct API)

**Description:** Baseline logs are created/updated only through schedule or earned value entry operations, not as standalone resources.

**Pros:**
- ✅ Simpler API surface
- ✅ Automatic baseline creation when baselining schedules/earned value

**Cons:**
- ❌ Doesn't meet PRD requirement for baseline management at milestones
- ❌ Cannot create baselines independently
- ❌ Limited flexibility
- ❌ Doesn't support baseline comparison requirements

**Estimated Complexity:** Low (but incomplete)

**Risk Factors:**
- High risk - doesn't meet PRD requirements

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### 5.1 Architectural Principles

**Principles Followed:**
- ✅ **Separation of Concerns:** Baseline Log is a distinct entity with clear responsibilities
- ✅ **Single Responsibility:** Each endpoint handles one operation
- ✅ **Consistency:** Follows established CRUD and project-scoped patterns
- ✅ **RESTful Design:** Standard HTTP methods (GET, POST, PUT, DELETE)
- ✅ **Schema Pattern:** Consistent Base/Create/Update/Public schema pattern

**Potential Violations:**
- None identified - approach follows existing patterns

### 5.2 Maintenance Burden

**Low Maintenance Areas:**
- Standard CRUD operations are well-understood
- Follows established patterns reduces learning curve
- Clear separation of concerns

**Potential Maintenance Concerns:**
- **Baseline Type Enum:** Currently stored as string with application-level validation. Consider database enum if types become more complex.
- **Soft Delete vs Hard Delete:** PRD says "no ability to delete events" but also mentions "events may be modified or cancelled". Need to clarify deletion policy.
- **Baseline Linking:** When schedules/earned value entries link to baselines, need to ensure referential integrity (what happens if baseline is deleted/cancelled?)

### 5.3 Testing Challenges

**Testable Aspects:**
- ✅ Standard CRUD operations are straightforward to test
- ✅ Project validation is easy to test (404 for non-existent project)
- ✅ Baseline type validation can be tested
- ✅ Relationship queries can be tested

**Challenging Aspects:**
- **Baseline Linking Logic:** Testing that schedules/earned value entries can link to baselines (requires integration tests)
- **Historical Baseline Integrity:** Testing that baselines remain immutable once linked (may need business logic validation)
- **Project Scoping:** Testing that users can only access baselines for projects they have access to (if permissions are added later)

**Test Coverage Strategy:**
- Unit tests for CRUD operations (similar to existing tests)
- Integration tests for baseline linking (schedule and earned value)
- Edge case tests: baseline without project, invalid baseline_type

### 5.4 Future Considerations

**Enhancements Needed Later:**
1. **Baseline Comparison Endpoints:** PRD requires comparison between baselines (E5-005 dependency)
2. **Baseline Snapshotting:** PRD mentions snapshot of budget/cost/revenue at baseline creation (may need BaselineSnapshot integration)
3. **Milestone Type Enum:** PRD lists standard milestones (kickoff, bom_release, etc.) - may need to add `milestone_type` field
4. **Permission System:** If role-based access is added, baseline creation may need project-level permissions
5. **Soft Delete/Cancellation:** Need to clarify deletion policy per PRD ("no deletion" vs "may be cancelled")

**Potential Refactoring:**
- If baseline types grow, consider database enum instead of string
- If baseline comparison becomes complex, may need dedicated comparison service
- If snapshotting is needed, may need to integrate with BaselineSnapshot model

---

## 6. RISKS AND UNKNOWNS

### 6.1 Identified Risks

1. **Migration Risk:** Adding `project_id`, `milestone_type`, `is_cancelled` to existing BaselineLog records (if any exist)
   - **Mitigation:** Check for existing records, handle migration gracefully with default values
   - **Impact:** Low if no existing data, Medium if data exists

2. **Baseline Deletion Policy:** ✅ **CLARIFIED** - Baselines can be soft deleted by marking as cancelled
   - **Implementation:** Add `is_cancelled` field, use PUT endpoint to cancel, filter cancelled baselines in list if needed
   - **Impact:** Low - straightforward soft delete pattern

3. **Baseline Linking Integrity:** What happens when a baseline is cancelled but schedules/earned value entries reference it?
   - **Mitigation:** Cancelled baselines remain in database (soft delete), so references remain valid. May need to add validation to prevent linking new schedules/entries to cancelled baselines.
   - **Impact:** Low-Medium - soft delete preserves referential integrity

4. **Missing Milestone Type:** ✅ **CLARIFIED** - Add `milestone_type` field
   - **Implementation:** Add `milestone_type` field with ENUM validation (kickoff, bom_release, engineering_complete, procurement_complete, manufacturing_start, shipment, site_arrival, commissioning_start, commissioning_complete, closeout)
   - **Impact:** Low - straightforward addition

### 6.2 Unknown Factors

1. **Baseline Creation Workflow:** ✅ **CLARIFIED** - Manual creation via UI with automatic snapshotting
   - **Implementation:** User creates baseline via UI, system automatically creates snapshot data

2. **Baseline Snapshotting:** ✅ **CLARIFIED** - Performed automatically when baselining, same operation includes snapshotting of budget/cost/revenues
   - **Implementation:** On baseline creation, automatically create BaselineSnapshot and BaselineCostElement records for all project cost elements
   - **Snapshot Data:** budget_bac, revenue_plan, actual_ac (aggregated from cost registrations), forecast_eac (if exists), earned_ev (if exists)

3. **Baseline Validation:** Should there be business rules about when baselines can be created/updated?
   - **Current Assumption:** Simple validation (project exists, baseline_type valid, milestone_type valid) for now, can add business rules later

4. **Frontend Integration Point:** ✅ **CLARIFIED** - Place UI in a specific tab in the project detail page
   - **Implementation:** Add "Baselines" tab to existing tabbed layout in project detail page

---

## 7. DEPENDENCIES AND BLOCKERS

### 7.1 Blocks

- **E3-007 (Earned Value Baseline Management):** Depends on E3-005 completion
- **E4-001 (Planned Value Calculation Engine):** May benefit from baseline linking for historical comparison

### 7.2 Dependencies

- **E1-001 (Database Schema):** ✅ Complete - BaselineLog model exists
- **E1-003 (Application Framework):** ✅ Complete - API routing patterns established
- **E2-003 (Cost Element Schedule):** ✅ Complete - Schedule model has baseline_id ready
- **E3-001 (Cost Registration):** ✅ Complete - No direct dependency but establishes patterns

### 7.3 No Blockers

- All prerequisite work is complete
- Model infrastructure is ready
- Related models (CostElementSchedule, EarnedValueEntry) already have baseline_id fields

---

## 8. SUMMARY AND RECOMMENDATIONS

### 8.1 Recommended Approach

**Approach 1: Project-Scoped CRUD API** is recommended because:
- Follows established architectural patterns
- Natural fit for PRD requirements (baselines belong to projects)
- Clear API hierarchy
- Consistent with existing codebase
- Low risk implementation

### 8.2 Implementation Phases

**Phase 1: Backend Model Update**
- Add `project_id`, `milestone_type`, `is_cancelled` to BaselineLog model
- Create migration
- Update schemas (Base/Create/Update/Public)

**Phase 2: Snapshotting Logic**
- Create helper function for automatic snapshotting
- On baseline creation: create BaselineSnapshot + BaselineCostElement records
- Snapshot all cost elements: budget_bac, revenue_plan, actual_ac, forecast_eac, earned_ev

**Phase 3: Backend API**
- Create CRUD endpoints (project-scoped)
- Add cancel endpoint (soft delete)
- Add validation logic (baseline_type, milestone_type enums)
- Write tests (including snapshotting tests)

**Phase 4: Frontend Components**
- Create baseline logs table/list component (with cancelled filter)
- Create add/edit/cancel modals (with milestone_type dropdown)
- Integrate into project detail page as dedicated tab

**Phase 5: Baseline Linking (Future)**
- E3-007 will link earned value entries to baselines
- Schedule baselining can be added when needed

### 8.3 Stakeholder Clarifications Received (2025-11-04)

✅ **All questions clarified:**

1. **Deletion Policy:** ✅ Baselines can be soft deleted by marking as cancelled (`is_cancelled=True`)
2. **Milestone Types:** ✅ Add `milestone_type` field (ENUM: kickoff, bom_release, engineering_complete, procurement_complete, manufacturing_start, shipment, site_arrival, commissioning_start, commissioning_complete, closeout)
3. **Baseline Snapshotting:** ✅ Performed automatically when baselining - same operation includes automatic snapshotting of budget/cost/revenues for all cost elements
4. **UI Placement:** ✅ Place UI in a specific tab in the project detail page

---

## 9. NEXT STEPS

1. ✅ **Stakeholder clarifications received** - All questions answered
2. **Create detailed implementation plan** following TDD approach
   - Include snapshotting logic in baseline creation
   - Add milestone_type field and validation
   - Implement soft delete (cancel) functionality
   - Plan tab integration in project detail page
3. **Begin Phase 1** (model update and migration)
4. **Implement automatic snapshotting** as part of baseline creation

---

**Document Status:** ✅ Analysis Complete - Ready for Detailed Planning
**Next Phase:** Detailed Planning (TDD implementation plan)
