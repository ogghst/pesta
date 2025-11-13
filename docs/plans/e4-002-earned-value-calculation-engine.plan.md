# Implementation Plan: E4-002 Earned Value Calculation Engine

**Task:** E4-002 - Earned Value Calculation Engine
**Sprint:** Sprint 4 - Earned Value Recording and Core EVM Calculations
**Status:** Planning Complete - Ready for Implementation
**Date:** 2025-11-13

---

## WORKING AGREEMENTS ACKNOWLEDGMENT

✅ **Test-Driven Development (TDD):** All code changes must be preceded by failing tests
✅ **Incremental Change:** Small, atomic commits (<100 lines, <5 files target)
✅ **Architectural Respect:** Follow existing patterns and abstractions (mirror E4-001 PV pattern)
✅ **No Code Duplication:** Reuse existing implementations where possible

---

## Objective

Implement Earned Value (EV) calculation engine computing EV = BAC × physical completion % from earned value entries at cost element, WBE, and project levels. This follows the E4-001 Planned Value pattern and enables future EVM performance indices (CPI, SPI) and variance calculations (CV, SV).

---

## Requirements Summary

**From Analysis Document:**
- ✅ **Recommended Approach:** Mirror Planned Value Architecture (E4-001 pattern)
- ✅ **Entry Selection:** Use most recent earned value entry where `completion_date ≤ control_date`
- ✅ **Percent Complete:** Each entry is a snapshot (use latest value, even if it decreases)
- ✅ **Baseline Integration:** Skip (defer to E3-007)
- ✅ **Zero EV Handling:** Return 0% complete, 0 EV for cost elements with no entries
- ✅ **Frontend Integration:** Required in Sprint 4

**Key Business Rules:**
- EV = BAC × (percent_complete / 100)
- Select most recent entry where `completion_date ≤ control_date` per cost element
- Aggregate EV and BAC up hierarchy (cost element → WBE → project)
- Weighted percent complete = total_EV / total_BAC at aggregated levels

---

## Implementation Approach

**Strategy:** Incremental Backend-First TDD (mirror E4-001 pattern)
1. **Phase 1:** Service layer - Pure calculation functions (TDD: failing tests first)
2. **Phase 2:** Response models - Schema definitions
3. **Phase 3:** API routes - FastAPI endpoints with database queries
4. **Phase 4:** Router registration - Wire up API routes
5. **Phase 5:** Frontend integration - Display EV metrics in UI

**Architecture Pattern:**
- Service layer: Pure functions (no database access) - `backend/app/services/earned_value.py`
- API layer: FastAPI routes with queries - `backend/app/api/routes/earned_value.py`
- Models layer: Response schemas - `backend/app/models/earned_value.py`
- Tests: Service unit tests + API integration tests

---

## IMPLEMENTATION STEPS

### PHASE 1: Service Layer (Backend)

#### Step 1.1: Create Service Module Structure

**Objective:** Create service module with constants and helper functions following PV pattern.

**Acceptance Criteria:**
- ✅ `backend/app/services/earned_value.py` exists
- ✅ Constants defined: `TWO_PLACES`, `FOUR_PLACES`, `ZERO`, `ONE`
- ✅ `_quantize()` helper function implemented
- ✅ `EarnedValueError` exception class defined
- ✅ File imports correctly (no syntax errors)

**Test-First Requirement:**
- None (infrastructure setup, no business logic yet)

**Files to Create:**
- `backend/app/services/earned_value.py`

**Dependencies:**
- None

**Estimated Time:** 15 minutes

---

#### Step 1.2: Implement Entry Selection Helper

**Objective:** Create function to find most recent earned value entry ≤ control_date for a cost element.

**Acceptance Criteria:**
- ✅ `_select_latest_entry_for_control_date()` function exists
- ✅ Returns most recent entry where `completion_date ≤ control_date`
- ✅ Returns `None` if no entries exist
- ✅ Returns `None` if all entries have `completion_date > control_date`
- ✅ Handles tie-breaking by `completion_date DESC, created_at DESC`

**Test-First Requirement:**
- Create test: `test_select_latest_entry_before_control_date()`
- Create test: `test_select_latest_entry_after_control_date_returns_none()`
- Create test: `test_select_latest_entry_no_entries_returns_none()`
- Create test: `test_select_latest_entry_tie_breaking()`

**Files to Create/Modify:**
- `backend/tests/services/test_earned_value.py` (new test file)
- `backend/app/services/earned_value.py` (implement function)

**Dependencies:**
- Step 1.1

**Estimated Time:** 1-2 hours

---

#### Step 1.3: Implement Earned Percent Complete Calculation

**Objective:** Calculate physical completion percent from earned value entry.

**Acceptance Criteria:**
- ✅ `calculate_earned_percent_complete()` function exists
- ✅ Returns `Decimal("0.0000")` if entry is `None`
- ✅ Returns `percent_complete / 100` from entry as Decimal
- ✅ Quantized to 4 decimal places
- ✅ Handles percent_complete = 0, 50, 100 correctly

**Test-First Requirement:**
- Create test: `test_calculate_earned_percent_complete_with_entry()`
- Create test: `test_calculate_earned_percent_complete_no_entry_returns_zero()`
- Create test: `test_calculate_earned_percent_complete_edge_cases()`

**Files to Modify:**
- `backend/app/services/earned_value.py`
- `backend/tests/services/test_earned_value.py`

**Dependencies:**
- Step 1.1, Step 1.2

**Estimated Time:** 30 minutes

---

#### Step 1.4: Implement Earned Value Calculation

**Objective:** Calculate EV = BAC × percent_complete for a cost element.

**Acceptance Criteria:**
- ✅ `calculate_earned_value()` function exists (enhance existing if needed)
- ✅ Formula: `EV = BAC × (percent_complete / 100)`
- ✅ Returns `Decimal("0.00")` if entry is `None`
- ✅ Quantized to 2 decimal places
- ✅ Handles BAC = 0, BAC = 100000, percent = 0, 50, 100 correctly

**Test-First Requirement:**
- Create test: `test_calculate_earned_value_uses_percent()`
- Create test: `test_calculate_earned_value_no_entry_returns_zero()`
- Create test: `test_calculate_earned_value_zero_bac()`

**Files to Modify:**
- `backend/app/services/earned_value.py`
- `backend/tests/services/test_earned_value.py`

**Dependencies:**
- Step 1.3

**Estimated Time:** 30 minutes

---

#### Step 1.5: Implement Cost Element Earned Value Wrapper

**Objective:** Calculate EV and percent for a cost element at control date.

**Acceptance Criteria:**
- ✅ `calculate_cost_element_earned_value()` function exists
- ✅ Takes `cost_element`, `entry`, `control_date` parameters
- ✅ Returns tuple `(earned_value: Decimal, percent_complete: Decimal)`
- ✅ Returns `(Decimal("0.00"), Decimal("0.0000"))` if entry is `None`
- ✅ Uses `cost_element.budget_bac` for BAC

**Test-First Requirement:**
- Create test: `test_calculate_cost_element_earned_value_with_entry()`
- Create test: `test_calculate_cost_element_earned_value_no_entry()`
- Create test: `test_calculate_cost_element_earned_value_zero_bac()`

**Files to Modify:**
- `backend/app/services/earned_value.py`
- `backend/tests/services/test_earned_value.py`

**Dependencies:**
- Step 1.4

**Estimated Time:** 30 minutes

---

#### Step 1.6: Implement Aggregation Logic

**Objective:** Aggregate EV values across multiple cost elements.

**Acceptance Criteria:**
- ✅ `AggregateResult` dataclass exists (mirror PV pattern)
- ✅ `aggregate_earned_value()` function exists
- ✅ Takes `Iterable[tuple[Decimal, Decimal]]` (EV, BAC pairs)
- ✅ Returns `AggregateResult` with `earned_value`, `percent_complete`, `budget_bac`
- ✅ Sums EV and BAC across tuples
- ✅ Calculates weighted percent = total_EV / total_BAC
- ✅ Returns `percent_complete = 0` if total_BAC = 0

**Test-First Requirement:**
- Create test: `test_aggregate_earned_value_sums_ev_and_bac()`
- Create test: `test_aggregate_earned_value_calculates_weighted_percent()`
- Create test: `test_aggregate_earned_value_zero_bac_returns_zero_percent()`
- Create test: `test_aggregate_earned_value_empty_list()`

**Files to Modify:**
- `backend/app/services/earned_value.py`
- `backend/tests/services/test_earned_value.py`

**Dependencies:**
- Step 1.5

**Estimated Time:** 1 hour

---

### PHASE 2: Response Models (Backend)

#### Step 2.1: Create Earned Value Response Models

**Objective:** Define response schemas for EV API endpoints.

**Acceptance Criteria:**
- ✅ `backend/app/models/earned_value.py` exists
- ✅ `EarnedValueBase` schema with: `level`, `control_date`, `earned_value`, `percent_complete`, `budget_bac`
- ✅ `EarnedValueCostElementPublic` extends base with `cost_element_id`
- ✅ `EarnedValueWBEPublic` extends base with `wbe_id`
- ✅ `EarnedValueProjectPublic` extends base with `project_id`
- ✅ All fields have correct types and constraints (mirror PV models)

**Test-First Requirement:**
- Create test: `test_earned_value_models_serialize_correctly()`
- Create test: `test_earned_value_models_validation()`

**Files to Create:**
- `backend/app/models/earned_value.py`

**Files to Modify:**
- `backend/app/models/__init__.py` (export new models)

**Dependencies:**
- Phase 1 complete (service layer ready)

**Estimated Time:** 30 minutes

---

### PHASE 3: API Routes (Backend)

#### Step 3.1: Create API Router Structure

**Objective:** Create FastAPI router with helper functions.

**Acceptance Criteria:**
- ✅ `backend/app/api/routes/earned_value.py` exists
- ✅ Router configured with prefix `/projects` and tag `earned-value`
- ✅ `_ensure_project_exists()` helper function (can reuse from PV)
- ✅ Imports service functions and models

**Test-First Requirement:**
- None (infrastructure setup)

**Files to Create:**
- `backend/app/api/routes/earned_value.py`

**Dependencies:**
- Step 2.1 (models ready)

**Estimated Time:** 15 minutes

---

#### Step 3.2: Implement Entry Selection Query Helper

**Objective:** Create function to query most recent entry per cost element for control date.

**Acceptance Criteria:**
- ✅ `_select_entry_for_cost_element()` function exists
- ✅ Takes `session`, `cost_element_id`, `control_date` parameters
- ✅ Returns most recent `EarnedValueEntry` where `completion_date ≤ control_date`
- ✅ Returns `None` if no entry exists
- ✅ Uses SQL query with ordering: `completion_date DESC, created_at DESC`

**Test-First Requirement:**
- Create API test: `test_select_entry_for_cost_element_finds_latest()`
- Create API test: `test_select_entry_for_cost_element_returns_none_if_none()`

**Files to Modify:**
- `backend/app/api/routes/earned_value.py`
- `backend/tests/api/routes/test_earned_value.py` (new test file)

**Dependencies:**
- Step 3.1

**Estimated Time:** 1 hour

---

#### Step 3.3: Implement Batch Entry Selection Helper

**Objective:** Create helper to query entries for multiple cost elements efficiently.

**Acceptance Criteria:**
- ✅ `_get_entry_map()` function exists
- ✅ Takes `session`, `cost_element_ids: list[uuid.UUID]`, `control_date` parameters
- ✅ Returns `dict[uuid.UUID, EarnedValueEntry | None]` mapping cost_element_id → entry
- ✅ Optimized query (single query with WHERE IN clause)
- ✅ Handles empty cost_element_ids list

**Test-First Requirement:**
- Create API test: `test_get_entry_map_batches_queries()`
- Create API test: `test_get_entry_map_empty_list()`

**Files to Modify:**
- `backend/app/api/routes/earned_value.py`
- `backend/tests/api/routes/test_earned_value.py`

**Dependencies:**
- Step 3.2

**Estimated Time:** 1 hour

---

#### Step 3.4: Implement Cost Element EV Endpoint

**Objective:** Create API endpoint for cost element earned value.

**Acceptance Criteria:**
- ✅ `GET /projects/{project_id}/earned-value/cost-elements/{cost_element_id}` endpoint exists
- ✅ Requires `control_date` query parameter
- ✅ Validates project exists (404 if not)
- ✅ Validates cost element exists and belongs to project (404 if not)
- ✅ Selects entry for cost element at control_date
- ✅ Calculates EV using service function
- ✅ Returns `EarnedValueCostElementPublic` response

**Test-First Requirement:**
- Create API test: `test_get_earned_value_for_cost_element()`
- Create API test: `test_get_earned_value_cost_element_no_entry_returns_zero()`
- Create API test: `test_get_earned_value_cost_element_not_found()`
- Create API test: `test_get_earned_value_requires_control_date()`

**Files to Modify:**
- `backend/app/api/routes/earned_value.py`
- `backend/tests/api/routes/test_earned_value.py`

**Dependencies:**
- Step 3.2, Step 1.5

**Estimated Time:** 1-2 hours

---

#### Step 3.5: Implement WBE EV Endpoint

**Objective:** Create API endpoint for WBE earned value (aggregated across cost elements).

**Acceptance Criteria:**
- ✅ `GET /projects/{project_id}/earned-value/wbes/{wbe_id}` endpoint exists
- ✅ Requires `control_date` query parameter
- ✅ Validates project and WBE exist (404 if not)
- ✅ Queries all cost elements for WBE
- ✅ Selects entries for all cost elements at control_date
- ✅ Calculates EV for each cost element
- ✅ Aggregates using service `aggregate_earned_value()` function
- ✅ Returns `EarnedValueWBEPublic` response

**Test-First Requirement:**
- Create API test: `test_get_earned_value_for_wbe()`
- Create API test: `test_get_earned_value_wbe_aggregates_cost_elements()`
- Create API test: `test_get_earned_value_wbe_no_entries_returns_zero()`
- Create API test: `test_get_earned_value_wbe_not_found()`

**Files to Modify:**
- `backend/app/api/routes/earned_value.py`
- `backend/tests/api/routes/test_earned_value.py`

**Dependencies:**
- Step 3.3, Step 3.4, Step 1.6

**Estimated Time:** 1-2 hours

---

#### Step 3.6: Implement Project EV Endpoint

**Objective:** Create API endpoint for project earned value (aggregated across all WBEs and cost elements).

**Acceptance Criteria:**
- ✅ `GET /projects/{project_id}/earned-value` endpoint exists
- ✅ Requires `control_date` query parameter
- ✅ Validates project exists (404 if not)
- ✅ Queries all WBEs for project
- ✅ Queries all cost elements for all WBEs
- ✅ Selects entries for all cost elements at control_date
- ✅ Calculates EV for each cost element
- ✅ Aggregates using service `aggregate_earned_value()` function
- ✅ Returns `EarnedValueProjectPublic` response

**Test-First Requirement:**
- Create API test: `test_get_earned_value_for_project()`
- Create API test: `test_get_earned_value_project_aggregates_across_wbes()`
- Create API test: `test_get_earned_value_project_no_entries_returns_zero()`
- Create API test: `test_get_earned_value_project_not_found()`

**Files to Modify:**
- `backend/app/api/routes/earned_value.py`
- `backend/tests/api/routes/test_earned_value.py`

**Dependencies:**
- Step 3.5

**Estimated Time:** 1-2 hours

---

### PHASE 4: Router Registration (Backend)

#### Step 4.1: Register Earned Value Router

**Objective:** Wire up earned value API routes in main router.

**Acceptance Criteria:**
- ✅ `backend/app/api/main.py` imports `earned_value` router
- ✅ `api_router.include_router(earned_value.router)` added
- ✅ Routes accessible at `/api/v1/projects/.../earned-value/...`
- ✅ OpenAPI schema generated correctly

**Test-First Requirement:**
- Create API test: `test_earned_value_routes_are_registered()`
- Verify OpenAPI schema includes new endpoints

**Files to Modify:**
- `backend/app/api/main.py`

**Dependencies:**
- Step 3.6

**Estimated Time:** 15 minutes

---

#### Step 4.2: Regenerate Frontend Client

**Objective:** Update frontend TypeScript client with new EV API endpoints.

**Acceptance Criteria:**
- ✅ Frontend client regenerated from OpenAPI schema
- ✅ TypeScript types for `EarnedValueCostElementPublic`, `EarnedValueWBEPublic`, `EarnedValueProjectPublic` exist
- ✅ Service functions exist: `getEarnedValueForCostElement()`, `getEarnedValueForWbe()`, `getEarnedValueForProject()`
- ✅ Client compiles without errors

**Test-First Requirement:**
- Verify TypeScript compilation succeeds
- Verify client exports new types and functions

**Files to Modify:**
- `frontend/src/client/` (regenerated files)

**Dependencies:**
- Step 4.1

**Estimated Time:** 5 minutes (regeneration)

---

### PHASE 5: Frontend Integration

#### Step 5.1: Create Earned Value Display Component (Cost Element Level)

**Objective:** Display EV metrics in cost element detail page.

**Acceptance Criteria:**
- ✅ Component displays: earned_value, percent_complete, budget_bac
- ✅ Fetches EV data using client service
- ✅ Handles loading and error states
- ✅ Displays "0%" if no earned value entries exist
- ✅ Uses control_date (can default to today)

**Test-First Requirement:**
- Manual testing: Navigate to cost element detail page
- Verify EV metrics display correctly
- Verify zero state displays correctly

**Files to Create/Modify:**
- `frontend/src/components/CostElements/EarnedValueSummary.tsx` (or integrate into existing component)

**Dependencies:**
- Step 4.2

**Estimated Time:** 2-3 hours

---

#### Step 5.2: Integrate EV into WBE Detail Page

**Objective:** Display aggregated EV metrics in WBE detail page.

**Acceptance Criteria:**
- ✅ WBE detail page displays aggregated EV
- ✅ Fetches EV data using WBE endpoint
- ✅ Displays earned_value, percent_complete, budget_bac
- ✅ Handles loading and error states

**Test-First Requirement:**
- Manual testing: Navigate to WBE detail page
- Verify aggregated EV displays correctly

**Files to Modify:**
- `frontend/src/components/WBEs/WBEDetail.tsx` (or create summary component)

**Dependencies:**
- Step 5.1

**Estimated Time:** 1-2 hours

---

#### Step 5.3: Integrate EV into Project Detail Page

**Objective:** Display aggregated EV metrics in project detail page.

**Acceptance Criteria:**
- ✅ Project detail page displays aggregated EV
- ✅ Fetches EV data using project endpoint
- ✅ Displays earned_value, percent_complete, budget_bac
- ✅ Handles loading and error states

**Test-First Requirement:**
- Manual testing: Navigate to project detail page
- Verify aggregated EV displays correctly

**Files to Modify:**
- `frontend/src/components/Projects/ProjectDetail.tsx` (or create summary component)

**Dependencies:**
- Step 5.2

**Estimated Time:** 1-2 hours

---

#### Step 5.4: Update Budget Timeline to Display EV

**Objective:** Integrate EV calculation into existing budget timeline visualization.

**Acceptance Criteria:**
- ✅ Budget timeline component can display EV alongside PV and AC
- ✅ EV data fetched for all cost elements in timeline
- ✅ Chart displays EV curve (likely already supported, verify)

**Test-First Requirement:**
- Manual testing: Open budget timeline
- Verify EV displays correctly
- Verify EV curve aligns with PV and AC

**Files to Modify:**
- `frontend/src/components/Projects/BudgetTimeline.tsx` (may already support EV)

**Dependencies:**
- Step 5.3

**Estimated Time:** 1-2 hours (may already be implemented)

---

## TDD DISCIPLINE RULES

1. **Failing Test First:** Every production code change must be preceded by a failing test
2. **Red-Green-Refactor:** Follow strict cycle:
   - Red: Write failing test
   - Green: Write minimal code to pass
   - Refactor: Improve code quality while keeping tests green
3. **Maximum Iterations:** Stop after 3 attempts per step to ask for help
4. **Behavior Verification:** Tests must verify behavior, not just compilation
5. **Test Coverage:** All service functions and API endpoints must have tests

## PROCESS CHECKPOINTS

**Checkpoint 1: After Phase 1 (Service Layer)**
- Pause and verify:
  - ✅ All service tests passing
  - ✅ Service functions match PV pattern
  - ✅ Edge cases handled correctly
  - Should we continue to Phase 2?

**Checkpoint 2: After Phase 3 (API Routes)**
- Pause and verify:
  - ✅ All API tests passing
  - ✅ Endpoints return correct data structures
  - ✅ Error handling works correctly
  - Should we continue to Phase 4?

**Checkpoint 3: After Phase 4 (Router Registration)**
- Pause and verify:
  - ✅ Client regenerated successfully
  - ✅ OpenAPI schema includes new endpoints
  - ✅ Backend fully functional
  - Should we continue to Phase 5 (Frontend)?

## SCOPE BOUNDARIES

**In Scope (E4-002):**
- ✅ EV calculation at cost element, WBE, project levels
- ✅ Entry selection logic (most recent ≤ control_date)
- ✅ Aggregation across hierarchy
- ✅ Frontend display of EV metrics
- ✅ Integration into existing detail pages

**Out of Scope (Deferred):**
- ❌ Baseline filtering (defer to E3-007)
- ❌ EVM performance indices (CPI, SPI) - E4-003
- ❌ Variance calculations (CV, SV) - E4-004
- ❌ Historical EV trends (future enhancement)
- ❌ EV export functionality (Sprint 5)

**Changes Requiring User Confirmation:**
- Any deviations from PV pattern must be approved
- Frontend UI/UX changes should be confirmed before implementation

## ROLLBACK STRATEGY

**Safe Rollback Points:**

1. **After Phase 1:** Service layer is isolated - can be removed without affecting API
   - Rollback: Delete `backend/app/services/earned_value.py` and tests
   - Impact: No impact on existing functionality

2. **After Phase 3:** API routes not yet registered - can be removed
   - Rollback: Delete `backend/app/api/routes/earned_value.py` and tests
   - Impact: No impact on existing functionality

3. **After Phase 4:** Router registered but no frontend usage
   - Rollback: Remove router registration from `main.py`
   - Impact: API endpoints unavailable, but no frontend breakage

4. **After Phase 5:** Frontend integration complete
   - Rollback: Revert frontend changes, remove router registration
   - Impact: Frontend loses EV display, but core functionality intact

**Alternative Approach (if rollback needed):**
- Keep service layer, refactor API to different pattern
- Or: Keep backend, defer frontend integration to Sprint 5

## ESTIMATED EFFORT

**Phase 1 (Service Layer):** 4-6 hours
**Phase 2 (Response Models):** 30 minutes
**Phase 3 (API Routes):** 5-8 hours
**Phase 4 (Router Registration):** 20 minutes
**Phase 5 (Frontend Integration):** 5-8 hours

**Total Estimated Effort:** 15-23 hours

## DEPENDENCIES

**Required (Blocking):**
- ✅ E3-006 (Earned Value Recording) - Complete
- ✅ E4-001 (Planned Value) - Complete (pattern reference)

**Optional (Non-blocking):**
- E3-002 (Cost Aggregation) - Provides aggregation pattern reference

## TEST COVERAGE REQUIREMENTS

**Service Layer Tests:**
- Entry selection logic (4+ tests)
- Percent calculation (3+ tests)
- EV calculation (3+ tests)
- Cost element wrapper (3+ tests)
- Aggregation (4+ tests)
- **Total: 17+ service tests**

**API Layer Tests:**
- Cost element endpoint (4+ tests)
- WBE endpoint (4+ tests)
- Project endpoint (4+ tests)
- Helper functions (2+ tests)
- **Total: 14+ API tests**

**Total Test Count Target:** 31+ tests

## COMPLETION CRITERIA

**E4-002 is complete when:**
- ✅ Service layer implements all EV calculation functions
- ✅ API endpoints return EV for cost element, WBE, project levels
- ✅ All tests passing (service + API)
- ✅ Frontend displays EV metrics in detail pages
- ✅ Integration with budget timeline (if applicable)
- ✅ Code follows E4-001 patterns
- ✅ No regressions in existing functionality

---

**Document Owner:** Development Team
**Review Status:** Ready for Implementation
**Next Step:** Begin Phase 1, Step 1.1 (Service Module Structure)
