# E3-008: Baseline Snapshot View UI - Detailed Implementation Plan

**Objective:** Create UI component to view baseline snapshot data for a selected baseline, displaying:
1. Overall project values (aggregated summary)
2. Table showing BaselineCostElement per WBE (grouped by WBE)
3. Table showing all BaselineCostElement records (flat list)

**Approach:** TDD with incremental commits (<100 lines, <5 files per commit)

**Estimated Time:** 20-28 hours

---

## Phase Overview

1. **Phase 1:** Backend API - Snapshot Summary Endpoint
2. **Phase 2:** Backend API - Cost Elements by WBE Endpoint
3. **Phase 3:** Backend API - Cost Elements List Endpoint
4. **Phase 4:** Frontend Client Generation
5. **Phase 5:** Frontend Component - BaselineSnapshotSummary
6. **Phase 6:** Frontend Component - BaselineCostElementsByWBETable
7. **Phase 7:** Frontend Component - BaselineCostElementsTable
8. **Phase 8:** Frontend Component - ViewBaselineSnapshot Modal
9. **Phase 9:** Integration - Add View Button to BaselineLogsTable

---

## Phase 1: Backend API - Snapshot Summary Endpoint

**Objective:** Create API endpoint to fetch baseline snapshot with aggregated project values

**Files to Create/Modify:**
1. `backend/app/api/routes/baseline_logs.py` - Add endpoint
2. `backend/tests/api/routes/test_baseline_logs.py` - Add tests

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 1.1:** Add response schema for snapshot summary
- Create `BaselineSnapshotSummaryPublic` schema in `backend/app/models/baseline_snapshot.py`
- Fields: `snapshot_id`, `baseline_id`, `baseline_date`, `milestone_type`, `description`, `total_budget_bac`, `total_revenue_plan`, `total_actual_ac`, `total_forecast_eac`, `total_earned_ev`, `cost_element_count`
- Add to `__init__.py` exports

**Commit 1.2:** Add endpoint implementation
- `GET /api/v1/projects/{project_id}/baseline-logs/{baseline_id}/snapshot`
- Validate project exists
- Validate baseline exists and belongs to project
- Get BaselineSnapshot linked to baseline_id
- Aggregate all BaselineCostElement records for this baseline:
  - Sum `budget_bac` → `total_budget_bac`
  - Sum `revenue_plan` → `total_revenue_plan`
  - Sum `actual_ac` → `total_actual_ac` (handle NULLs)
  - Sum `forecast_eac` → `total_forecast_eac` (handle NULLs)
  - Sum `earned_ev` → `total_earned_ev` (handle NULLs)
  - Count BaselineCostElement records → `cost_element_count`
- Return `BaselineSnapshotSummaryPublic`

**Commit 1.3:** Add tests for snapshot summary endpoint
- Test successful retrieval with all aggregated values
- Test with NULL values in actual_ac, forecast_eac, earned_ev
- Test baseline not found (404)
- Test baseline belongs to different project (404)
- Test project not found (404)
- Test snapshot not found (should still work if baseline exists but no snapshot)

**Estimated Time:** 3-4 hours
**Test Target:** 6 tests passing

---

## Phase 2: Backend API - Cost Elements by WBE Endpoint

**Objective:** Create API endpoint to fetch BaselineCostElement records grouped by WBE

**Files to Create/Modify:**
1. `backend/app/api/routes/baseline_logs.py` - Add endpoint
2. `backend/tests/api/routes/test_baseline_logs.py` - Add tests

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 2.1:** Add response schema for grouped data
- Create `BaselineCostElementWithCostElementPublic` schema (extends BaselineCostElementPublic with CostElement fields)
- Fields from BaselineCostElement: `budget_bac`, `revenue_plan`, `actual_ac`, `forecast_eac`, `earned_ev`, `baseline_cost_element_id`, `cost_element_id`
- Fields from CostElement: `department_code`, `department_name`, `cost_element_type_id` (via join)
- Create `WBEWithBaselineCostElementsPublic` schema
- Fields: `wbe_id`, `machine_type`, `serial_number`, `cost_elements: list[BaselineCostElementWithCostElementPublic]`, `wbe_total_budget_bac`, `wbe_total_revenue_plan`, `wbe_total_actual_ac`, `wbe_total_forecast_eac`, `wbe_total_earned_ev`
- Create `BaselineCostElementsByWBEPublic` schema
- Fields: `baseline_id`, `wbes: list[WBEWithBaselineCostElementsPublic]`
- Add to `__init__.py` exports

**Commit 2.2:** Add endpoint implementation
- `GET /api/v1/projects/{project_id}/baseline-logs/{baseline_id}/cost-elements-by-wbe`
- Validate project exists
- Validate baseline exists and belongs to project
- Get all WBEs for the project
- For each WBE:
  - Get all BaselineCostElement records for this baseline + WBE (via CostElement join)
  - Join with CostElement to get department_code, department_name, cost_element_type_id
  - Aggregate WBE totals (sum of all cost elements in WBE)
- Return `BaselineCostElementsByWBEPublic`

**Commit 2.3:** Add tests for cost elements by WBE endpoint
- Test successful retrieval with multiple WBEs
- Test WBE with no cost elements (empty list)
- Test aggregation accuracy (sums match)
- Test baseline not found (404)
- Test baseline belongs to different project (404)
- Test project not found (404)

**Estimated Time:** 4-5 hours
**Test Target:** 6 tests passing

---

## Phase 3: Backend API - Cost Elements List Endpoint

**Objective:** Create API endpoint to fetch all BaselineCostElement records (flat list with pagination)

**Files to Create/Modify:**
1. `backend/app/api/routes/baseline_logs.py` - Add endpoint
2. `backend/tests/api/routes/test_baseline_logs.py` - Add tests

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 3.1:** Add response schema for paginated list
- Create `BaselineCostElementsPublic` schema (similar to other paginated responses)
- Fields: `data: list[BaselineCostElementWithCostElementPublic]`, `count: int`
- Add WBE fields to `BaselineCostElementWithCostElementPublic`: `wbe_id`, `wbe_machine_type` (via CostElement → WBE join)
- Add to `__init__.py` exports

**Commit 3.2:** Add endpoint implementation
- `GET /api/v1/projects/{project_id}/baseline-logs/{baseline_id}/cost-elements`
- Query params: `skip: int = 0`, `limit: int = 100`
- Validate project exists
- Validate baseline exists and belongs to project
- Get all BaselineCostElement records for this baseline
- Join with CostElement to get department_code, department_name, cost_element_type_id
- Join with WBE to get wbe_id, machine_type
- Apply pagination (skip/limit)
- Count total records (for pagination)
- Return `BaselineCostElementsPublic`

**Commit 3.3:** Add tests for cost elements list endpoint
- Test successful retrieval with pagination
- Test pagination (skip/limit)
- Test count accuracy
- Test empty list (no cost elements)
- Test baseline not found (404)
- Test baseline belongs to different project (404)
- Test project not found (404)

**Estimated Time:** 3-4 hours
**Test Target:** 7 tests passing

---

## Phase 4: Frontend Client Generation

**Objective:** Regenerate TypeScript client with new API endpoints

**Files to Modify:**
1. `frontend/src/client/sdk.gen.ts` - Auto-generated
2. `frontend/src/client/types.gen.ts` - Auto-generated
3. `frontend/src/client/schemas.gen.ts` - Auto-generated

**Commits:**

**Commit 4.1:** Regenerate client
- Run `scripts/generate-client.sh`
- Verify new service methods: `BaselineLogsService.getBaselineSnapshotSummary()`, `BaselineLogsService.getBaselineCostElementsByWbe()`, `BaselineLogsService.getBaselineCostElements()`
- Verify new types: `BaselineSnapshotSummaryPublic`, `BaselineCostElementsByWBEPublic`, `BaselineCostElementsPublic`, `BaselineCostElementWithCostElementPublic`, `WBEWithBaselineCostElementsPublic`

**Estimated Time:** 15 minutes
**Test Target:** TypeScript compilation succeeds

---

## Phase 5: Frontend Component - BaselineSnapshotSummary

**Objective:** Create summary cards component showing aggregated project values

**Files to Create:**
1. `frontend/src/components/Projects/BaselineSnapshotSummary.tsx`

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 5.1:** Create BaselineSnapshotSummary component structure
- Similar to `BudgetSummary` / `CostSummary` components
- Use `Grid` layout with 4-5 cards
- Fetch data using TanStack Query: `BaselineLogsService.getBaselineSnapshotSummary()`
- Display cards:
  - Total Budget BAC
  - Total Revenue Plan
  - Total Actual AC (if available)
  - Total Forecast EAC (if available)
  - Total Earned EV (if available)
- Format currency values: `€{value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
- Loading state with `SkeletonText`
- Empty state handling

**Commit 5.2:** Add styling and polish
- Match existing summary card styling (border, padding, colors)
- Add metadata display (baseline_date, milestone_type, description)
- Handle NULL values gracefully (show "N/A" or hide card)

**Estimated Time:** 2-3 hours
**Test Target:** Component renders, displays data, handles loading/error

---

## Phase 6: Frontend Component - BaselineCostElementsByWBETable

**Objective:** Create grouped table component showing BaselineCostElement records by WBE

**Files to Create:**
1. `frontend/src/components/Projects/BaselineCostElementsByWBETable.tsx`

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 6.1:** Create component structure
- Use `Accordion` or `Collapsible` from Chakra UI for WBE grouping
- Fetch data using TanStack Query: `BaselineLogsService.getBaselineCostElementsByWbe()`
- For each WBE:
  - Display WBE header (machine_type, serial_number)
  - Display WBE totals (aggregated values)
  - Nested table with BaselineCostElement records
- Use `DataTable` component for nested tables
- Columns: Department, Cost Element Type, Budget BAC, Revenue Plan, Actual AC, Forecast EAC, Earned EV

**Commit 6.2:** Add table columns and formatting
- Define column definitions for BaselineCostElement table
- Format currency values
- Handle NULL values (show "N/A")
- Add sorting and filtering (optional)

**Estimated Time:** 3-4 hours
**Test Target:** Component renders, groups by WBE, displays nested tables

---

## Phase 7: Frontend Component - BaselineCostElementsTable

**Objective:** Create flat table component showing all BaselineCostElement records

**Files to Create:**
1. `frontend/src/components/Projects/BaselineCostElementsTable.tsx`

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 7.1:** Create component structure
- Use `DataTable` component
- Fetch data using TanStack Query: `BaselineLogsService.getBaselineCostElements()`
- Implement pagination (50-100 items per page)
- Columns: WBE, Department, Cost Element Type, Budget BAC, Revenue Plan, Actual AC, Forecast EAC, Earned EV
- Handle pagination state (page, setPage)

**Commit 7.2:** Add table columns and formatting
- Define column definitions
- Format currency values
- Handle NULL values (show "N/A")
- Add sorting and filtering
- Format dates (if needed)

**Estimated Time:** 2-3 hours
**Test Target:** Component renders, displays paginated data, pagination works

---

## Phase 8: Frontend Component - ViewBaselineSnapshot Modal

**Objective:** Create main modal component with tabs orchestrating all three views

**Files to Create:**
1. `frontend/src/components/Projects/ViewBaselineSnapshot.tsx`

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 8.1:** Create modal structure
- Use `DialogRoot` / `DialogContent` pattern (following `EditBaselineLog`)
- Use `Tabs` component from Chakra UI
- Three tabs: "Summary", "By WBE", "All Cost Elements"
- Size: `xl` to accommodate tables
- Props: `baselineId: string`, `projectId: string`
- Controlled open state: `useState(false)` with `isOpen`

**Commit 8.2:** Integrate sub-components
- Tab 1: Render `BaselineSnapshotSummary` component
- Tab 2: Render `BaselineCostElementsByWBETable` component
- Tab 3: Render `BaselineCostElementsTable` component
- Lazy load data when tab is activated (use `enabled: tab === "summary"` in queries)
- Handle loading states per tab
- Add "Close" button in footer

**Commit 8.3:** Add trigger button and polish
- Add `DialogTrigger` with "View" button (FiEye icon)
- Button styling: `variant="ghost" size="sm"`
- Add baseline info in header (baseline_date, milestone_type, description)
- Handle error states

**Estimated Time:** 3-4 hours
**Test Target:** Modal opens, tabs switch, data loads per tab

---

## Phase 9: Integration - Add View Button to BaselineLogsTable

**Objective:** Integrate ViewBaselineSnapshot component into BaselineLogsTable

**Files to Modify:**
1. `frontend/src/components/Projects/BaselineLogsTable.tsx`

**Commits (Target: <100 lines, <5 files per commit):**

**Commit 9.1:** Add View button to actions column
- Import `ViewBaselineSnapshot` component
- Add "View" button in actions column (FiEye icon)
- Place between Edit and Cancel buttons
- Pass `baselineId` and `projectId` props
- Button styling: `variant="ghost" size="sm"`

**Estimated Time:** 30 minutes
**Test Target:** View button appears, opens modal on click

---

## Test Checklist

### Backend Tests

- [ ] Snapshot summary endpoint returns aggregated values correctly
- [ ] Snapshot summary handles NULL values in actual_ac, forecast_eac, earned_ev
- [ ] Cost elements by WBE endpoint groups correctly
- [ ] Cost elements by WBE aggregates WBE totals correctly
- [ ] Cost elements list endpoint paginates correctly
- [ ] Cost elements list endpoint counts correctly
- [ ] All endpoints validate project ownership
- [ ] All endpoints handle missing baseline (404)
- [ ] All endpoints handle missing project (404)

### Frontend Tests

- [ ] BaselineSnapshotSummary renders summary cards
- [ ] BaselineSnapshotSummary handles loading state
- [ ] BaselineSnapshotSummary handles NULL values
- [ ] BaselineCostElementsByWBETable groups by WBE
- [ ] BaselineCostElementsByWBETable displays nested tables
- [ ] BaselineCostElementsTable displays paginated data
- [ ] BaselineCostElementsTable pagination works
- [ ] ViewBaselineSnapshot modal opens/closes
- [ ] ViewBaselineSnapshot tabs switch correctly
- [ ] ViewBaselineSnapshot lazy loads data per tab
- [ ] ViewBaselineSnapshot handles errors gracefully
- [ ] View button appears in BaselineLogsTable
- [ ] View button opens modal correctly

---

## Implementation Notes

1. **Data Aggregation:** Use SQLModel aggregation functions (`sum()`, `count()`) for efficient database queries
2. **NULL Handling:** All aggregation endpoints should handle NULL values (use `COALESCE` or Python `sum()` with `None` handling)
3. **Joins:** CostElements → WBEs joins needed for grouping and display
4. **Pagination:** Flat table should use 50-100 items per page (configurable)
5. **Caching:** TanStack Query will cache data per tab, reducing redundant API calls
6. **Lazy Loading:** Only fetch data when tab is activated (use `enabled` in `useQuery`)
7. **Error Handling:** All components should handle 404, 500 errors gracefully
8. **Loading States:** All components should show loading skeletons while fetching

---

## Risk Mitigation

1. **Large Datasets:** Pagination in flat table prevents performance issues
2. **Complex Joins:** Test with realistic data (multiple WBEs, cost elements)
3. **NULL Values:** Aggregation logic must handle NULLs correctly
4. **Modal Size:** Use `xl` size and ensure responsive design
5. **Tab Switching:** Lazy loading prevents unnecessary API calls

---

**Total Estimated Time:** 20-28 hours

**Ready for Implementation:** Yes
