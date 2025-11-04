# Implementation Plan: E3-005 Baseline Log Implementation

**Task:** E3-005 - Baseline Log Implementation
**Sprint:** Sprint 3 - Cost Registration and Data Entry
**Status:** Planning Complete - Ready for Implementation
**Date:** 2025-11-04

---

## Objective

Build a baseline tracking system for schedule and earned value baselines. Implement CRUD operations for Baseline Log with automatic snapshotting of budget/cost/revenue data when baselines are created. Enable soft delete (cancellation) and integrate baseline management UI into project detail page as a dedicated tab.

---

## Requirements Summary

**From PRD (Section 10.1 - 10.3):**
- System shall support creation of cost and schedule baselines at significant project milestones
- Baseline events must capture: baseline date, event description, event classification (milestone type), responsible department
- System shall maintain all historical baselines for comparison
- Baseline Log shall maintain complete event history (no hard deletion)

**From Stakeholder Clarifications (2025-11-04):**
- ✅ **Snapshotting:** Performed automatically when baselining - same operation includes automatic snapshotting of budget/cost/revenues for all cost elements
- ✅ **Deletion:** A baseline can be soft deleted by marking as cancelled (`is_cancelled=True`)
- ✅ **Milestone Types:** Add `milestone_type` field (ENUM: kickoff, bom_release, engineering_complete, procurement_complete, manufacturing_start, shipment, site_arrival, commissioning_start, commissioning_complete, closeout)
- ✅ **UI Placement:** Place UI in a specific tab in the project detail page

**From Analysis:**
- BaselineLog model exists but missing `project_id`, `milestone_type`, `is_cancelled` fields
- CostElementSchedule and EarnedValueEntry already have `baseline_id` ready for linking
- BaselineSnapshot model exists but needs to be linked to BaselineLog
- BaselineCostElement model needs to be created for snapshotting cost element state

---

## Implementation Approach

**Strategy:** Incremental Enhancement (Backend-First TDD)
- Update model and create migration first
- Create snapshotting helper function
- Implement CRUD API endpoints with snapshotting
- Build frontend components
- Integrate into project detail page tab

**Architecture Pattern:**
- Backend: Project-scoped CRUD endpoints following `budget_summary.py` pattern
- Snapshotting: Automatic creation of BaselineSnapshot + BaselineCostElement records on baseline creation
- Frontend: Table component with add/edit/cancel modals
- Integration: Dedicated "Baselines" tab in project detail page

**TDD Discipline:**
- Write failing tests first for each phase
- Target <100 lines, <5 files per commit
- Comprehensive test coverage for snapshotting logic

---

## Data Model Analysis

### BaselineLog Model Updates

**Fields to Add:**
- `project_id` (UUID, FK → Project, NOT NULL)
- `milestone_type` (STRING, max_length=100, NOT NULL)
- `is_cancelled` (BOOLEAN, default=False)

**Enum Values:**
- `baseline_type`: schedule, earned_value, budget, forecast, combined
- `milestone_type`: kickoff, bom_release, engineering_complete, procurement_complete, manufacturing_start, shipment, site_arrival, commissioning_start, commissioning_complete, closeout

### Snapshotting Data Model

**BaselineSnapshot:**
- Already exists with: `snapshot_id`, `project_id`, `baseline_date`, `milestone_type`, `description`, `department`, `is_pmb`, `created_by_id`, `created_at`
- **Update:** Add `baseline_id` (UUID, FK → BaselineLog, nullable) to link snapshot to log entry

**BaselineCostElement (NEW):**
- `baseline_cost_element_id` (UUID, PK)
- `baseline_id` (UUID, FK → BaselineLog, NOT NULL) - Link to baseline log entry
- `cost_element_id` (UUID, FK → CostElement, NOT NULL)
- `budget_bac` (DECIMAL(15,2)) - Snapshot of cost_element.budget_bac
- `revenue_plan` (DECIMAL(15,2)) - Snapshot of cost_element.revenue_plan
- `actual_ac` (DECIMAL(15,2), nullable) - Aggregated from cost_registrations
- `forecast_eac` (DECIMAL(15,2), nullable) - From forecast if exists
- `earned_ev` (DECIMAL(15,2), nullable) - From earned_value_entries if exists
- `created_at` (TIMESTAMP)

**Snapshotting Logic:**
- On baseline creation, for each cost element in project:
  - Get current `budget_bac` and `revenue_plan` from CostElement
  - Aggregate `actual_ac` from CostRegistration records
  - Get `forecast_eac` from Forecast if exists (is_current=True)
  - Get `earned_ev` from EarnedValueEntry if exists (latest entry)
  - Create BaselineCostElement record with snapshot values

---

## Phase Breakdown

### Phase 1: Backend Model Update - BaselineLog

**Objective:** Add missing fields to BaselineLog model and update schemas

**Files to Modify:**
1. `backend/app/models/baseline_log.py` - Add fields and update schemas

**Test Files:**
1. `backend/tests/models/test_baseline_log.py` - Update existing tests

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 1.1:** Update BaselineLogBase schema
- Add `milestone_type: str` field (max_length=100)
- Add `is_cancelled: bool` field (default=False)
- Keep existing fields: `baseline_type`, `baseline_date`, `description`

**Commit 1.2:** Update BaselineLogCreate schema
- Add `project_id: uuid.UUID` field
- Keep existing `created_by_id` field

**Commit 1.3:** Update BaselineLog model
- Add `project_id: uuid.UUID` field with foreign key to `project.project_id`
- Add `milestone_type: str` field
- Add `is_cancelled: bool` field (default=False)
- Add `project: Project | None` relationship
- Import Project model

**Commit 1.4:** Update BaselineLogPublic schema
- Add `project_id`, `milestone_type`, `is_cancelled` fields
- Keep existing fields: `baseline_id`, `created_by_id`, `created_at`

**Commit 1.5:** Update BaselineLogUpdate schema
- Make `milestone_type` and `is_cancelled` optional
- Keep existing optional fields

**Commit 1.6:** Update existing tests
- Update `test_create_baseline_log()` to include `project_id` and `milestone_type`
- Add test for `is_cancelled` field default
- Add test for milestone_type validation

**Estimated Time:** 1-2 hours
**Test Target:** All existing tests passing + new field tests

---

### Phase 2: Database Migration

**Objective:** Create Alembic migration for schema changes

**Files to Create:**
1. `backend/alembic/versions/XXXX_add_project_id_milestone_type_is_cancelled_to_baseline_log.py`

**Commits:**

**Commit 2.1:** Create migration script
- Add `project_id` column (UUID, NOT NULL, FK to project.project_id)
- Add `milestone_type` column (STRING(100), NOT NULL)
- Add `is_cancelled` column (BOOLEAN, default=False)
- Add index on `project_id` for query performance
- Add index on `is_cancelled` for filtering cancelled baselines
- Handle existing data: set default `milestone_type` to 'kickoff' if records exist, set `is_cancelled=False`

**Commit 2.2:** Apply migration and verify
- Run migration: `alembic upgrade head`
- Verify schema changes in database
- Check indexes created

**Estimated Time:** 30 minutes
**Test Target:** Migration applies successfully, no data loss

---

### Phase 3: Create BaselineCostElement Model

**Objective:** Create model for snapshotting cost element state at baseline creation

**Files to Create:**
1. `backend/app/models/baseline_cost_element.py` - Model and schemas

**Files to Modify:**
1. `backend/app/models/__init__.py` - Export new models

**Test Files:**
1. `backend/tests/models/test_baseline_cost_element.py` - New test file

**Commits:**

**Commit 3.1:** Create BaselineCostElementBase schema
- Fields: `budget_bac`, `revenue_plan`, `actual_ac?`, `forecast_eac?`, `earned_ev?`
- Use Decimal for monetary values (DECIMAL(15,2))

**Commit 3.2:** Create BaselineCostElementCreate schema
- Add `baseline_id: uuid.UUID`, `cost_element_id: uuid.UUID`
- Extends BaselineCostElementBase

**Commit 3.3:** Create BaselineCostElement model
- Primary key: `baseline_cost_element_id`
- Foreign keys: `baseline_id` → BaselineLog, `cost_element_id` → CostElement
- Relationships: `baseline_log`, `cost_element`
- Timestamp: `created_at`

**Commit 3.4:** Create BaselineCostElementPublic schema
- Include all fields + `baseline_cost_element_id`, `created_at`

**Commit 3.5:** Export models in __init__.py
- Add imports and exports

**Commit 3.6:** Write model tests
- Test: `test_create_baseline_cost_element()`
- Test: `test_baseline_cost_element_relationships()`
- Test: `test_baseline_cost_element_decimal_fields()`

**Estimated Time:** 1-2 hours
**Test Target:** 3-4 tests passing

---

### Phase 4: Update BaselineSnapshot Model

**Objective:** Link BaselineSnapshot to BaselineLog via baseline_id

**Files to Modify:**
1. `backend/app/models/baseline_snapshot.py` - Add baseline_id field

**Test Files:**
1. `backend/tests/models/test_baseline_snapshot.py` - Update tests

**Commits:**

**Commit 4.1:** Add baseline_id to BaselineSnapshot model
- Add `baseline_id: uuid.UUID | None` field (nullable foreign key to BaselineLog)
- Add `baseline_log: BaselineLog | None` relationship
- Import BaselineLog model

**Commit 4.2:** Update BaselineSnapshotPublic schema
- Add `baseline_id` field (optional)

**Commit 4.3:** Create migration for baseline_id
- Add `baseline_id` column (UUID, nullable, FK to baselinelog.baseline_id)
- Add index on `baseline_id`

**Commit 4.4:** Update tests
- Test: `test_baseline_snapshot_with_baseline_log()`
- Test: `test_baseline_snapshot_without_baseline_log()` (nullable)

**Estimated Time:** 1 hour
**Test Target:** All tests passing

---

### Phase 5: Snapshotting Helper Function

**Objective:** Create helper function to automatically snapshot cost element data when baseline is created

**Files to Create:**
1. `backend/app/api/routes/baseline_logs.py` - New router file (partial)

**Files to Modify:**
1. None yet (helper function only)

**Commits:**

**Commit 5.1:** Create snapshotting helper function
- Function: `create_baseline_snapshot_for_baseline_log()`
- Parameters: `session`, `baseline_log`, `created_by_id`
- Logic:
  1. Create BaselineSnapshot record with project_id, baseline_date, milestone_type, description
  2. Get all cost elements for project (via WBEs)
  3. For each cost element:
     - Get budget_bac, revenue_plan from CostElement
     - Aggregate actual_ac from CostRegistration records
     - Get forecast_eac from Forecast (is_current=True) if exists
     - Get earned_ev from EarnedValueEntry (latest by completion_date) if exists
     - Create BaselineCostElement record
  4. Return BaselineSnapshot

**Commit 5.2:** Write tests for snapshotting function
- Test: `test_create_baseline_snapshot_with_cost_elements()`
- Test: `test_create_baseline_snapshot_with_no_cost_elements()`
- Test: `test_create_baseline_snapshot_aggregates_actual_cost()`
- Test: `test_create_baseline_snapshot_includes_forecast_eac_if_exists()`
- Test: `test_create_baseline_snapshot_includes_earned_ev_if_exists()`

**Estimated Time:** 2-3 hours
**Test Target:** 5 tests passing

---

### Phase 6: Backend API - List and Read Endpoints

**Objective:** Create GET endpoints for listing and reading baselines

**Files to Modify:**
1. `backend/app/api/routes/baseline_logs.py` - Add endpoints
2. `backend/app/api/main.py` - Register router

**Test Files:**
1. `backend/tests/api/routes/test_baseline_logs.py` - New test file

**Commits:**

**Commit 6.1:** Add failing tests for list endpoint
- Test: `test_list_baseline_logs_for_project()`
- Test: `test_list_baseline_logs_empty_project()`
- Test: `test_list_baseline_logs_project_not_found()`
- Test: `test_list_baseline_logs_filters_cancelled()` (optional filter)

**Commit 6.2:** Implement list endpoint
- Endpoint: `GET /api/v1/projects/{project_id}/baseline-logs/`
- Function: `list_baseline_logs()`
- Query: Filter by project_id, optionally filter out cancelled (is_cancelled=False)
- Response: List of BaselineLogPublic
- Validation: Check project exists, return 404 if not

**Commit 6.3:** Add failing tests for read endpoint
- Test: `test_read_baseline_log()`
- Test: `test_read_baseline_log_not_found()`
- Test: `test_read_baseline_log_wrong_project()`

**Commit 6.4:** Implement read endpoint
- Endpoint: `GET /api/v1/projects/{project_id}/baseline-logs/{baseline_id}`
- Function: `read_baseline_log()`
- Validation: Check baseline exists and belongs to project
- Response: BaselineLogPublic

**Commit 6.5:** Register router in main.py
- Import baseline_logs router
- Add `api_router.include_router(baseline_logs.router)`

**Estimated Time:** 2-3 hours
**Test Target:** 7-8 tests passing

---

### Phase 7: Backend API - Create Endpoint with Snapshotting

**Objective:** Create POST endpoint that creates baseline and automatically snapshots data

**Files to Modify:**
1. `backend/app/api/routes/baseline_logs.py` - Add create endpoint

**Test Files:**
1. `backend/tests/api/routes/test_baseline_logs.py` - Add create tests

**Commits:**

**Commit 7.1:** Add failing tests for create endpoint
- Test: `test_create_baseline_log()`
- Test: `test_create_baseline_log_with_snapshotting()`
- Test: `test_create_baseline_log_project_not_found()`
- Test: `test_create_baseline_log_invalid_baseline_type()`
- Test: `test_create_baseline_log_invalid_milestone_type()`

**Commit 7.2:** Implement create endpoint
- Endpoint: `POST /api/v1/projects/{project_id}/baseline-logs/`
- Function: `create_baseline_log()`
- Validation:
  - Check project exists
  - Validate baseline_type enum (schedule, earned_value, budget, forecast, combined)
  - Validate milestone_type enum (kickoff, bom_release, engineering_complete, procurement_complete, manufacturing_start, shipment, site_arrival, commissioning_start, commissioning_complete, closeout)
- Create BaselineLog record
- Call `create_baseline_snapshot_for_baseline_log()` helper
- Return BaselineLogPublic

**Commit 7.3:** Add snapshotting integration tests
- Test: `test_create_baseline_snapshots_all_cost_elements()`
- Test: `test_create_baseline_snapshots_actual_cost_aggregated()`
- Test: `test_create_baseline_snapshot_with_empty_project()`

**Estimated Time:** 2-3 hours
**Test Target:** 8-9 tests passing

---

### Phase 8: Backend API - Update and Cancel Endpoints

**Objective:** Create PUT endpoints for updating and cancelling baselines

**Files to Modify:**
1. `backend/app/api/routes/baseline_logs.py` - Add update and cancel endpoints

**Test Files:**
1. `backend/tests/api/routes/test_baseline_logs.py` - Add update/cancel tests

**Commits:**

**Commit 8.1:** Add failing tests for update endpoint
- Test: `test_update_baseline_log()`
- Test: `test_update_baseline_log_not_found()`
- Test: `test_update_baseline_log_wrong_project()`
- Test: `test_update_baseline_log_invalid_baseline_type()`

**Commit 8.2:** Implement update endpoint
- Endpoint: `PUT /api/v1/projects/{project_id}/baseline-logs/{baseline_id}`
- Function: `update_baseline_log()`
- Validation: Check baseline exists and belongs to project
- Update only provided fields (exclude_unset=True)
- Return updated BaselineLogPublic

**Commit 8.3:** Add failing tests for cancel endpoint
- Test: `test_cancel_baseline_log()`
- Test: `test_cancel_baseline_log_not_found()`
- Test: `test_cancel_baseline_log_already_cancelled()`

**Commit 8.4:** Implement cancel endpoint
- Endpoint: `PUT /api/v1/projects/{project_id}/baseline-logs/{baseline_id}/cancel`
- Function: `cancel_baseline_log()`
- Set `is_cancelled=True`
- Return updated BaselineLogPublic

**Estimated Time:** 1-2 hours
**Test Target:** 6-7 tests passing

---

### Phase 9: Frontend Client Generation

**Objective:** Generate TypeScript client with new endpoints

**Files to Modify:**
1. Run `scripts/generate-client.sh` to regenerate OpenAPI client

**Commits:**

**Commit 9.1:** Regenerate frontend client
- Run client generation script
- Verify new `BaselineLogsService` and types exported
- Verify project-scoped endpoint paths
- Verify BaselineLogPublic, BaselineLogCreate, BaselineLogUpdate schemas

**Estimated Time:** 15 minutes

---

### Phase 10: Frontend Components - BaselineLogsTable

**Objective:** Create table component for listing baselines

**Files to Create:**
1. `frontend/src/components/Projects/BaselineLogsTable.tsx` - Table component

**Commits:**

**Commit 10.1:** Create BaselineLogsTable component structure
- Use DataTable component (following existing pattern)
- Columns: baseline_date, baseline_type, milestone_type, description, is_cancelled, created_by, actions
- Use TanStack Query to fetch baselines
- Handle loading and error states

**Commit 10.2:** Add table actions and styling
- Add visual indicator for cancelled baselines (strikethrough or badge)
- Add row click navigation (if needed)
- Add sorting and filtering
- Format dates: `toLocaleDateString()`
- Format cancelled status (badge or icon)

**Estimated Time:** 2-3 hours
**Test Target:** Component renders, displays data, handles loading/error

---

### Phase 11: Frontend Components - AddBaselineLog Modal

**Objective:** Create modal for adding new baselines

**Files to Create:**
1. `frontend/src/components/Projects/AddBaselineLog.tsx` - Create modal

**Commits:**

**Commit 11.1:** Create AddBaselineLog modal structure
- Use DialogRoot/DialogContent pattern (following AddProject/AddWBE)
- Form fields: baseline_type (select), baseline_date (date picker), milestone_type (select), description (textarea)
- Use React Hook Form for form management
- Use TanStack Query mutation for create

**Commit 11.2:** Add validation and submission
- Validate required fields (baseline_type, baseline_date, milestone_type)
- Validate enum values (dropdown options)
- Submit form, show toast on success/error
- Invalidate queries to refresh table
- Close modal on success

**Estimated Time:** 2 hours
**Test Target:** Modal opens, form validates, submission works

---

### Phase 12: Frontend Components - EditBaselineLog and CancelBaselineLog

**Objective:** Create modals for editing and cancelling baselines

**Files to Create:**
1. `frontend/src/components/Projects/EditBaselineLog.tsx` - Edit modal
2. `frontend/src/components/Projects/CancelBaselineLog.tsx` - Cancel confirmation

**Commits:**

**Commit 12.1:** Create EditBaselineLog modal
- Similar to AddBaselineLog but pre-populated with existing data
- Fetch baseline data on open
- Update mutation instead of create
- Handle loading state during fetch

**Commit 12.2:** Create CancelBaselineLog confirmation
- Confirmation dialog pattern (following DeleteWBE)
- Warning message about soft delete
- Cancel mutation (PUT to /cancel endpoint)
- Refresh table on success

**Estimated Time:** 2 hours
**Test Target:** Edit modal works, cancel confirmation works

---

### Phase 13: Integration into Project Detail Page

**Objective:** Add Baselines tab to project detail page

**Files to Modify:**
1. `frontend/src/routes/_layout/projects.$id.tsx` - Add baselines tab

**Commits:**

**Commit 13.1:** Add baselines tab to tabbed layout
- Add "baselines" to tab enum in search schema
- Add Tab component for baselines
- Import BaselineLogsTable, AddBaselineLog, EditBaselineLog, CancelBaselineLog components
- Add "Create Baseline" button in tab header

**Commit 13.2:** Integrate components in baselines tab
- Render BaselineLogsTable in tab content
- Add action buttons (Edit, Cancel) in table actions column
- Wire up AddBaselineLog modal trigger
- Wire up EditBaselineLog and CancelBaselineLog modals
- Follow existing tab pattern (Info, WBEs, etc.)

**Commit 13.3:** Add styling and polish
- Ensure responsive design
- Match existing tab styling
- Add proper spacing and layout
- Test tab navigation

**Estimated Time:** 2-3 hours
**Test Target:** Tab appears, components work, navigation smooth

---

## Test Checklist

### Backend Tests

- [ ] Model tests: BaselineLog with new fields (project_id, milestone_type, is_cancelled)
- [ ] Model tests: BaselineCostElement creation and relationships
- [ ] Model tests: BaselineSnapshot with baseline_id
- [ ] Migration tests: Schema changes applied correctly
- [ ] Snapshotting tests: Helper function creates snapshots correctly
- [ ] Snapshotting tests: Aggregates actual_ac from cost registrations
- [ ] Snapshotting tests: Includes forecast_eac if exists
- [ ] Snapshotting tests: Includes earned_ev if exists
- [ ] API tests: List baselines for project
- [ ] API tests: Read single baseline
- [ ] API tests: Create baseline with snapshotting
- [ ] API tests: Update baseline
- [ ] API tests: Cancel baseline (soft delete)
- [ ] API tests: Validation (project not found, invalid enums)
- [ ] API tests: Project-scoped filtering works correctly

### Frontend Tests

- [ ] Component: BaselineLogsTable renders correctly
- [ ] Component: BaselineLogsTable handles loading/error states
- [ ] Component: AddBaselineLog modal opens and validates
- [ ] Component: AddBaselineLog submits successfully
- [ ] Component: EditBaselineLog pre-populates and updates
- [ ] Component: CancelBaselineLog confirms and cancels
- [ ] Integration: Baselines tab appears in project detail page
- [ ] Integration: Tab navigation works
- [ ] Integration: All modals work from tab context

---

## Estimated Time Summary

| Phase | Description | Time Estimate |
|-------|-------------|---------------|
| Phase 1 | Backend Model Update | 1-2 hours |
| Phase 2 | Database Migration | 30 minutes |
| Phase 3 | Create BaselineCostElement Model | 1-2 hours |
| Phase 4 | Update BaselineSnapshot Model | 1 hour |
| Phase 5 | Snapshotting Helper Function | 2-3 hours |
| Phase 6 | Backend API - List/Read | 2-3 hours |
| Phase 7 | Backend API - Create with Snapshotting | 2-3 hours |
| Phase 8 | Backend API - Update/Cancel | 1-2 hours |
| Phase 9 | Frontend Client Generation | 15 minutes |
| Phase 10 | Frontend - BaselineLogsTable | 2-3 hours |
| Phase 11 | Frontend - AddBaselineLog | 2 hours |
| Phase 12 | Frontend - Edit/Cancel Modals | 2 hours |
| Phase 13 | Integration - Project Detail Tab | 2-3 hours |
| **Total** | | **18-25 hours** |

---

## Dependencies

### Prerequisites
- ✅ E1-001: Database Schema Implementation (complete)
- ✅ E1-003: Application Framework Setup (complete)
- ✅ E2-003: Cost Element Schedule Management (complete)
- ✅ E3-001: Cost Registration Interface (complete)
- ✅ E3-002: Cost Aggregation Logic (complete)

### Blocks
- E3-007: Earned Value Baseline Management (depends on E3-005)
- E4-001: Planned Value Calculation Engine (may benefit from baseline linking)

---

## Risks and Mitigation

1. **Snapshotting Complexity:** Aggregating actual_ac from multiple cost registrations
   - **Mitigation:** Follow cost_summary.py aggregation pattern, test thoroughly

2. **Migration of Existing Data:** If BaselineLog records exist, need to set defaults
   - **Mitigation:** Check for existing records, handle gracefully with default values

3. **BaselineCostElement Model:** New model needs to be created
   - **Mitigation:** Follow existing model patterns, comprehensive tests

4. **Frontend Tab Integration:** Need to match existing tab patterns
   - **Mitigation:** Study existing tab implementation, follow exact pattern

---

## Success Criteria

- ✅ BaselineLog model has project_id, milestone_type, is_cancelled fields
- ✅ Migration applies successfully with no data loss
- ✅ BaselineCostElement model created and tested
- ✅ Snapshotting automatically creates BaselineSnapshot + BaselineCostElement records
- ✅ All CRUD endpoints work correctly (list, read, create, update, cancel)
- ✅ Frontend table displays baselines with proper formatting
- ✅ Add/Edit/Cancel modals work correctly
- ✅ Baselines tab integrated into project detail page
- ✅ All tests passing (backend + frontend)
- ✅ No regressions in existing functionality

---

**Document Status:** ✅ Ready for Implementation
**Next Step:** Begin Phase 1 - Backend Model Update (TDD: failing tests first)
