# Detailed Implementation Plan: E4-007 Cost Performance Report

**Task:** E4-007 - Cost Performance Report
**Sprint:** Sprint 5 - Reporting and Performance Dashboards
**Status:** Planning Phase
**Date:** 2025-11-17
**Current Time:** 06:51 CET (Europe/Rome)
**Approach:** Approach A - Dedicated Report Component with New API Endpoint

---

## EXECUTION CONTEXT

- This plan will be implemented using TDD discipline with human supervision
- Implementation will occur in steps within this conversation thread
- Each step must have clear stop/go criteria
- Maximum 3 iteration attempts per step before stopping to ask for help
- Red-green-refactor cycle must be followed for each step
- Tests must verify behavior, not just compilation

---

## SCOPE BOUNDARIES

**In Scope:**
- Backend API endpoint for cost performance report data
- Frontend report component using DataTable with TanStack Table
- Tabular display of all EVM metrics (PV, EV, AC, BAC, CPI, SPI, TCPI, CV, SV)
- Project-level report with drill-down to WBE and cost element detail pages
- Color-coded status indicators for CPI, SPI, TCPI, CV, SV
- Time-machine integration (control date filtering)
- Client-side sorting and filtering (minimal filters: WBE, department)
- Scalable filter architecture for future enhancements
- Summary rows showing aggregated totals at project level
- Responsive design (mobile, tablet, desktop)

**Out of Scope (MVP):**
- Export functionality (CSV, Excel) - deferred to E4-010
- Period performance calculations (1-year period) - future enhancement
- Server-side pagination (not needed for 30-40 WBEs, up to 200 cost elements)
- Advanced filtering (date ranges, cost element types) - future enhancement
- WBE-level and cost element-level dedicated report pages - future enhancement
- Report scheduling or email delivery

**Design for Future:**
- Filter architecture should support server-side filtering extension
- Data structure should support period performance (1-year) addition
- Component structure should support export functionality integration

---

## STAKEHOLDER CLARIFICATIONS

- **Typical Project Size:** 30-40 WBEs, up to 200 cost elements
- **Filter Requirements:** Minimal filters at first (WBE, department), scalable design for future
- **Export:** Not needed for MVP (deferred to E4-010)
- **Period Performance:** 1-year period definition (future enhancement)

---

## IMPLEMENTATION STEPS

### Phase 1: Backend API Endpoint

#### Step 1: Define Report Response Model

**Description:** Create Pydantic response model for cost performance report data structure. Each row represents a cost element with all EVM metrics and hierarchical metadata.

**Test-First Requirement:**
- Write failing test that verifies model structure:
  - Required fields: cost_element_id, wbe_id, wbe_name, department_code, department_name, and all EVM metrics
  - Optional fields: serial_number, cost_element_type
  - Data types: UUIDs, strings, Decimals, optional None values for CPI/SPI/TCPI
  - Test model serialization/deserialization

**Acceptance Criteria:**
- ✅ New model file: `backend/app/models/cost_performance_report.py`
- ✅ Model class: `CostPerformanceReportRowPublic` with all required fields:
  - `cost_element_id: uuid.UUID`
  - `wbe_id: uuid.UUID`
  - `wbe_name: str` (machine_type)
  - `wbe_serial_number: str | None`
  - `department_code: str`
  - `department_name: str`
  - `cost_element_type_id: uuid.UUID | None`
  - `cost_element_type_name: str | None`
  - All EVM metrics: `planned_value`, `earned_value`, `actual_cost`, `budget_bac`, `cpi`, `spi`, `tcpi`, `cost_variance`, `schedule_variance`
- ✅ Model class: `CostPerformanceReportPublic` containing:
  - `project_id: uuid.UUID`
  - `project_name: str`
  - `control_date: date`
  - `rows: list[CostPerformanceReportRowPublic]`
  - `summary: EVMIndicesProjectPublic` (aggregated project totals)
- ✅ Models exported in `backend/app/models/__init__.py`
- ✅ Test passes verifying model structure and serialization

**Expected Files Created:**
- `backend/app/models/cost_performance_report.py`
- `backend/tests/models/test_cost_performance_report.py`

**Expected Files Modified:**
- `backend/app/models/__init__.py`

**Dependencies:**
- None (first step)

**Estimated Effort:** 1-2 hours

---

#### Step 2: Create Report Service Function

**Description:** Create service function that aggregates EVM metrics for all cost elements in a project, returning report rows. Reuses existing `EvmMetricsService` aggregation logic.

**Test-First Requirement:**
- Write failing test that verifies:
  - Function signature: `get_cost_performance_report(session, project_id, control_date) -> CostPerformanceReportPublic`
  - Returns all cost elements with EVM metrics
  - Includes project summary with aggregated totals
  - Respects time-machine control date (filters cost elements created after control date)
  - Handles empty project (returns empty rows list, zero summary)
  - Handles project with no cost elements

**Acceptance Criteria:**
- ✅ New service file: `backend/app/services/cost_performance_report.py`
- ✅ Function: `get_cost_performance_report(session, project_id, control_date) -> CostPerformanceReportPublic`
- ✅ Reuses existing `get_cost_element_evm_metrics()` from `evm_aggregation.py`
- ✅ Queries all cost elements for project (respecting control date)
- ✅ For each cost element, calls `get_cost_element_evm_metrics()` to get EVM metrics
- ✅ Includes WBE metadata (machine_type, serial_number) in each row
- ✅ Includes cost element metadata (department_code, department_name, cost_element_type)
- ✅ Aggregates project summary using existing `get_project_evm_metrics()` function
- ✅ Returns `CostPerformanceReportPublic` with rows and summary
- ✅ Test passes verifying function returns correct data structure

**Expected Files Created:**
- `backend/app/services/cost_performance_report.py`
- `backend/tests/services/test_cost_performance_report.py`

**Dependencies:**
- Step 1 (response model)

**Estimated Effort:** 2-3 hours

---

#### Step 3: Create Report API Endpoint

**Description:** Create FastAPI endpoint that exposes the cost performance report via REST API.

**Test-First Requirement:**
- Write failing API test that verifies:
  - Endpoint: `GET /api/v1/projects/{project_id}/reports/cost-performance`
  - Returns 200 with `CostPerformanceReportPublic` response
  - Returns 404 for non-existent project
  - Respects time-machine control date (via dependency injection)
  - Requires authentication (CurrentUser dependency)
  - Returns correct data structure matching service function output

**Acceptance Criteria:**
- ✅ New router file: `backend/app/api/routes/cost_performance_report.py`
- ✅ Endpoint: `GET /projects/{project_id}/reports/cost-performance`
- ✅ Response model: `CostPerformanceReportPublic`
- ✅ Dependencies: `SessionDep`, `CurrentUser`, `get_time_machine_control_date`
- ✅ Calls `get_cost_performance_report()` service function
- ✅ Returns 404 for non-existent project
- ✅ Router registered in `backend/app/api/main.py`
- ✅ Test passes verifying endpoint returns correct response

**Expected Files Created:**
- `backend/app/api/routes/cost_performance_report.py`
- `backend/tests/api/routes/test_cost_performance_report.py`

**Expected Files Modified:**
- `backend/app/api/main.py` (router registration)

**Dependencies:**
- Step 2 (service function)

**Estimated Effort:** 2-3 hours

---

#### Step 4: Regenerate OpenAPI Client

**Description:** Regenerate frontend OpenAPI client to include new report endpoint and types.

**Test-First Requirement:**
- Verify TypeScript types are generated correctly:
  - `CostPerformanceReportPublic` type exists
  - `CostPerformanceReportRowPublic` type exists
  - `CostPerformanceReportService` with `getProjectCostPerformanceReportEndpoint()` method

**Acceptance Criteria:**
- ✅ Run OpenAPI client generation script
- ✅ New types generated in `frontend/src/client/types.gen.ts`
- ✅ New service generated in `frontend/src/client/sdk.gen.ts`
- ✅ TypeScript compilation succeeds
- ✅ Types match backend response models

**Expected Files Modified:**
- `frontend/src/client/types.gen.ts`
- `frontend/src/client/sdk.gen.ts`
- `frontend/src/client/index.ts`

**Dependencies:**
- Step 3 (API endpoint)

**Estimated Effort:** 15 minutes

---

### Phase 2: Frontend Report Component

#### Step 5: Create Report Component Structure

**Description:** Create basic `CostPerformanceReport` component structure with data fetching using React Query.

**Test-First Requirement:**
- Write failing test that verifies:
  - Component renders without errors
  - Component makes API call to `CostPerformanceReportService.getProjectCostPerformanceReportEndpoint()`
  - Query key includes project_id and control_date
  - Loading state displays skeleton/loading indicator
  - Error state displays error message

**Acceptance Criteria:**
- ✅ New component file: `frontend/src/components/Reports/CostPerformanceReport.tsx`
- ✅ Component props: `{ projectId: string }`
- ✅ Uses `useQuery` with `CostPerformanceReportService.getProjectCostPerformanceReportEndpoint()`
- ✅ Query key: `["cost-performance-report", projectId, controlDate]`
- ✅ Time-machine integration via `useTimeMachine()` hook
- ✅ Loading state with skeleton/loading indicator
- ✅ Error state with error message display
- ✅ Empty state handling (no cost elements)
- ✅ Test passes verifying component structure and data fetching

**Expected Files Created:**
- `frontend/src/components/Reports/CostPerformanceReport.tsx`
- `frontend/src/components/Reports/__tests__/CostPerformanceReport.test.tsx` (or similar)

**Dependencies:**
- Step 4 (OpenAPI client)

**Estimated Effort:** 1-2 hours

---

#### Step 6: Define Table Column Definitions

**Description:** Define TanStack Table column definitions for all EVM metrics with proper formatting and cell renderers.

**Test-First Requirement:**
- Write failing test that verifies:
  - Column definitions include all required columns
  - Columns have correct accessor keys
  - Columns have proper header labels
  - Currency columns format values correctly
  - Percentage columns format values correctly
  - Index columns (CPI, SPI, TCPI) format decimals correctly
  - Status indicator columns render color-coded cells

**Acceptance Criteria:**
- ✅ Column definitions array created with type: `ColumnDefExtended<CostPerformanceReportRowPublic>[]`
- ✅ Hierarchy columns:
  - WBE Name (machine_type)
  - WBE Serial Number (optional, show if available)
  - Department Code
  - Department Name
- ✅ Core metric columns:
  - BAC (Budget at Completion) - currency format
  - PV (Planned Value) - currency format
  - EV (Earned Value) - currency format
  - AC (Actual Cost) - currency format
- ✅ Performance index columns:
  - CPI (Cost Performance Index) - decimal format, color-coded
  - SPI (Schedule Performance Index) - decimal format, color-coded
  - TCPI (To-Complete Performance Index) - decimal or 'overrun', color-coded
- ✅ Variance columns:
  - CV (Cost Variance) - currency format, color-coded
  - SV (Schedule Variance) - currency format, color-coded
- ✅ Percent complete columns (optional):
  - EV/BAC % - percentage format
  - PV/BAC % - percentage format
- ✅ All columns have proper cell renderers with formatting
- ✅ Test passes verifying column definitions

**Expected Files Modified:**
- `frontend/src/components/Reports/CostPerformanceReport.tsx`

**Dependencies:**
- Step 5 (component structure)

**Estimated Effort:** 2-3 hours

---

#### Step 7: Integrate DataTable Component

**Description:** Integrate existing `DataTable` component with column definitions and report data.

**Test-First Requirement:**
- Write failing test that verifies:
  - DataTable renders with report data
  - All columns are visible
  - Data is displayed correctly in table cells
  - Sorting works on all sortable columns
  - Row click navigation works (drill-down to cost element detail page)

**Acceptance Criteria:**
- ✅ Import `DataTable` component
- ✅ Pass report rows data to `DataTable`
- ✅ Pass column definitions to `DataTable`
- ✅ Configure row click handler for navigation:
  - Navigate to `/projects/{projectId}/wbes/{wbeId}/cost-elements/{costElementId}`
- ✅ Table displays all rows correctly
- ✅ Sorting enabled on all numeric columns
- ✅ Test passes verifying table rendering and interactivity

**Expected Files Modified:**
- `frontend/src/components/Reports/CostPerformanceReport.tsx`

**Dependencies:**
- Step 6 (column definitions)

**Estimated Effort:** 1-2 hours

---

#### Step 8: Add Status Indicator Cell Renderers

**Description:** Create cell renderers for CPI, SPI, TCPI, CV, SV columns with color-coded status indicators.

**Test-First Requirement:**
- Write failing test that verifies:
  - CPI cell renderer shows correct color (red/yellow/green) based on value
  - SPI cell renderer shows correct color (red/yellow/green) based on value
  - TCPI cell renderer shows correct color and handles 'overrun' string
  - CV cell renderer shows correct color (red/yellow/green) based on value
  - SV cell renderer shows correct color (red/yellow/green) based on value
  - Null/None values display as "N/A" with gray color

**Acceptance Criteria:**
- ✅ Reuse or extract status indicator helpers from `EarnedValueSummary.tsx`:
  - `getCpiStatus()`, `getSpiStatus()`, `getTcpiStatus()`, `getCvStatus()`, `getSvStatus()`
- ✅ Create cell renderer functions that:
  - Call status indicator helper
  - Render value with color-coded background or border
  - Display icon (optional) and formatted value
  - Handle null/None values gracefully
- ✅ Apply cell renderers to CPI, SPI, TCPI, CV, SV columns
- ✅ Color thresholds match business rules:
  - CPI/SPI: < 0.95 (red), 0.95-1.0 (yellow), ≥ 1.0 (green)
  - TCPI: ≤ 1.0 (green), 1.0-1.1 (yellow), > 1.1 or 'overrun' (red)
  - CV/SV: < 0 (red), = 0 (yellow), > 0 (green)
- ✅ Test passes verifying status indicators render correctly

**Expected Files Modified:**
- `frontend/src/components/Reports/CostPerformanceReport.tsx`
- Optionally: `frontend/src/utils/evmStatusIndicators.ts` (if extracting helpers)

**Dependencies:**
- Step 7 (DataTable integration)

**Estimated Effort:** 2-3 hours

---

#### Step 9: Add Summary Row

**Description:** Add summary row at bottom of table showing aggregated project totals.

**Test-First Requirement:**
- Write failing test that verifies:
  - Summary row displays at bottom of table
  - Summary row shows aggregated totals from report summary
  - Summary row has distinct styling (bold, different background)
  - Summary row columns align with data columns

**Acceptance Criteria:**
- ✅ Extract summary data from report response (`report.summary`)
- ✅ Create summary row renderer that:
  - Displays "Project Total" or similar label in hierarchy columns
  - Displays aggregated values in metric columns
  - Uses distinct styling (bold text, different background color)
- ✅ Render summary row after all data rows in table
- ✅ Summary row is not sortable or clickable
- ✅ Test passes verifying summary row displays correctly

**Expected Files Modified:**
- `frontend/src/components/Reports/CostPerformanceReport.tsx`

**Dependencies:**
- Step 8 (status indicators)

**Estimated Effort:** 1-2 hours

---

#### Step 10: Add Client-Side Filtering (Scalable Design)

**Description:** Add minimal client-side filtering (WBE, department) with scalable architecture for future server-side filtering.

**Test-First Requirement:**
- Write failing test that verifies:
  - Filter controls render (WBE dropdown, department dropdown)
  - Filtering by WBE shows only rows for selected WBE
  - Filtering by department shows only rows for selected department
  - Multiple filters work together (AND logic)
  - Clear filters button resets all filters
  - Filter state persists during component lifecycle

**Acceptance Criteria:**
- ✅ Create filter state management (useState hooks)
- ✅ Create filter UI components:
  - WBE multi-select dropdown (populated from report data)
  - Department multi-select dropdown (populated from report data)
  - Clear filters button
- ✅ Apply filters to report rows (client-side filtering)
- ✅ Filter architecture designed for future extension:
  - Filter state structure supports server-side filtering parameters
  - Filter UI components are modular and reusable
  - Filter logic is separated from component (extractable to hook)
- ✅ Filters work with DataTable (filtered data passed to table)
- ✅ Test passes verifying filtering functionality

**Expected Files Modified:**
- `frontend/src/components/Reports/CostPerformanceReport.tsx`
- Optionally: `frontend/src/hooks/useReportFilters.ts` (if extracting filter logic)

**Dependencies:**
- Step 9 (summary row)

**Estimated Effort:** 2-3 hours

---

### Phase 3: Integration and Navigation

#### Step 11: Create Report Route

**Description:** Create new route for cost performance report page.

**Test-First Requirement:**
- Write failing test that verifies:
  - Route renders `CostPerformanceReport` component
  - Route accepts project_id parameter
  - Route displays report header with project name
  - Route displays control date from time-machine

**Acceptance Criteria:**
- ✅ New route file: `frontend/src/routes/_layout/projects.$id.reports.cost-performance.tsx`
- ✅ Route uses `CostPerformanceReport` component
- ✅ Route displays report header:
  - Project name
  - Report title: "Cost Performance Report"
  - Control date (from time-machine)
  - Report generation timestamp (optional)
- ✅ Route integrates with project detail navigation
- ✅ Test passes verifying route renders correctly

**Expected Files Created:**
- `frontend/src/routes/_layout/projects.$id.reports.cost-performance.tsx`

**Dependencies:**
- Step 10 (filtering)

**Estimated Effort:** 1-2 hours

---

#### Step 12: Add Navigation Links

**Description:** Add navigation links to report from project detail page.

**Test-First Requirement:**
- Write failing test that verifies:
  - Navigation link appears in project detail page
  - Clicking link navigates to report page
  - Link is visible and accessible

**Acceptance Criteria:**
- ✅ Add "Reports" tab or link in project detail page
- ✅ Link navigates to `/projects/{projectId}/reports/cost-performance`
- ✅ Link is styled consistently with other navigation elements
- ✅ Link is accessible (keyboard navigation, screen readers)
- ✅ Test passes verifying navigation works

**Expected Files Modified:**
- `frontend/src/routes/_layout/projects.$id.tsx` (project detail page)

**Dependencies:**
- Step 11 (report route)

**Estimated Effort:** 1 hour

---

#### Step 13: Add Drill-Down Navigation

**Description:** Implement row click navigation from report to cost element detail page.

**Test-First Requirement:**
- Write failing test that verifies:
  - Clicking a row navigates to cost element detail page
  - Navigation URL is correct: `/projects/{projectId}/wbes/{wbeId}/cost-elements/{costElementId}`
  - Navigation preserves time-machine control date (if applicable)

**Acceptance Criteria:**
- ✅ Configure `onRowClick` handler in DataTable
- ✅ Handler extracts cost_element_id and wbe_id from row data
- ✅ Handler navigates using TanStack Router:
  - Route: `/projects/$id/wbes/$wbeId/cost-elements/$costElementId`
  - Preserves query parameters (control date if in URL)
- ✅ Navigation works from all report rows
- ✅ Test passes verifying drill-down navigation

**Expected Files Modified:**
- `frontend/src/components/Reports/CostPerformanceReport.tsx`

**Dependencies:**
- Step 12 (navigation links)

**Estimated Effort:** 1 hour

---

### Phase 4: Testing and Refinement

#### Step 14: Backend Integration Tests

**Description:** Write comprehensive backend integration tests for report endpoint.

**Test-First Requirement:**
- Write integration tests covering:
  - Report with multiple WBEs and cost elements
  - Report with empty project (no cost elements)
  - Report with single cost element
  - Time-machine control date filtering
  - Aggregation accuracy (compare with individual EVM metrics)
  - Edge cases (null values, zero values, 'overrun' TCPI)

**Acceptance Criteria:**
- ✅ Integration test file: `backend/tests/api/routes/test_cost_performance_report.py`
- ✅ Tests cover:
  - Happy path: report with multiple cost elements
  - Empty project: returns empty rows, zero summary
  - Single cost element: returns one row
  - Time-machine: filters cost elements created after control date
  - Aggregation: summary totals match project EVM metrics
  - Edge cases: null CPI/SPI, 'overrun' TCPI, zero values
- ✅ All tests pass
- ✅ Test coverage > 80% for report endpoint

**Expected Files Modified:**
- `backend/tests/api/routes/test_cost_performance_report.py`

**Dependencies:**
- Step 3 (API endpoint)

**Estimated Effort:** 2-3 hours

---

#### Step 15: Frontend Component Tests

**Description:** Write comprehensive frontend component tests for report component.

**Test-First Requirement:**
- Write component tests covering:
  - Component rendering with data
  - Loading state
  - Error state
  - Empty state
  - Table rendering with all columns
  - Sorting functionality
  - Filtering functionality
  - Row click navigation
  - Status indicator rendering

**Acceptance Criteria:**
- ✅ Component test file: `frontend/src/components/Reports/__tests__/CostPerformanceReport.test.tsx`
- ✅ Tests cover:
  - Rendering with mock data
  - Loading skeleton display
  - Error message display
  - Empty state message
  - Table columns and data display
  - Sorting on numeric columns
  - Filtering by WBE and department
  - Row click navigation
  - Status indicator colors
  - Summary row display
- ✅ All tests pass
- ✅ Test coverage > 70% for component

**Expected Files Modified:**
- `frontend/src/components/Reports/__tests__/CostPerformanceReport.test.tsx`

**Dependencies:**
- Step 13 (drill-down navigation)

**Estimated Effort:** 2-3 hours

---

#### Step 16: End-to-End Integration Test

**Description:** Write Playwright end-to-end test for complete report workflow.

**Test-First Requirement:**
- Write E2E test that verifies:
  - Navigate to project detail page
  - Click "Reports" link
  - Report page loads and displays data
  - Table shows all cost elements
  - Sorting works
  - Filtering works
  - Row click navigates to cost element detail
  - Summary row displays correctly

**Acceptance Criteria:**
- ✅ E2E test file: `frontend/tests/reports/cost-performance-report.spec.ts`
- ✅ Test covers:
  - Navigation to report page
  - Report data loading
  - Table interaction (sorting, filtering)
  - Drill-down navigation
  - Visual verification of status indicators
- ✅ Test passes in Playwright
- ✅ Test is stable and reliable

**Expected Files Created:**
- `frontend/tests/reports/cost-performance-report.spec.ts`

**Dependencies:**
- Step 15 (component tests)

**Estimated Effort:** 2-3 hours

---

#### Step 17: Responsive Design and Polish

**Description:** Ensure report component is responsive and polished for production.

**Test-First Requirement:**
- Manual testing and visual verification:
  - Mobile view (narrow screen)
  - Tablet view (medium screen)
  - Desktop view (wide screen)
  - Table scrolling and column visibility
  - Filter UI on mobile devices

**Acceptance Criteria:**
- ✅ Report component is responsive:
  - Mobile: Table scrolls horizontally, filters stack vertically
  - Tablet: Table uses available space, filters in row
  - Desktop: Full table width, filters in horizontal layout
- ✅ Column visibility menu works on all screen sizes
- ✅ Table is readable and accessible on all devices
- ✅ Loading and error states are user-friendly
- ✅ Visual polish: Consistent spacing, colors, typography
- ✅ Manual testing confirms responsive behavior

**Expected Files Modified:**
- `frontend/src/components/Reports/CostPerformanceReport.tsx`

**Dependencies:**
- Step 16 (E2E test)

**Estimated Effort:** 2-3 hours

---

## PROCESS CHECKPOINTS

**Checkpoint 1: After Step 4 (Backend Complete)**
- Pause and verify:
  - Backend API endpoint returns correct data structure
  - OpenAPI client generated successfully
  - Backend tests passing
  - Should we continue with frontend implementation?

**Checkpoint 2: After Step 10 (Frontend Core Complete)**
- Pause and verify:
  - Report component renders with data
  - Table displays all columns correctly
  - Filtering works as expected
  - Should we continue with integration and testing?

**Checkpoint 3: After Step 16 (All Features Complete)**
- Pause and verify:
  - All tests passing (backend, frontend, E2E)
  - Manual testing successful
  - Ready for production deployment?

---

## ROLLBACK STRATEGY

**Safe Rollback Points:**

1. **After Step 4 (Backend Complete):**
   - Backend API endpoint is complete and tested
   - Can be used independently or by other frontend implementations
   - Rollback: Remove frontend changes, keep backend endpoint

2. **After Step 10 (Frontend Core Complete):**
   - Report component is functional with basic features
   - Can be used without navigation integration
   - Rollback: Remove navigation links, keep component

**Alternative Approaches if Current Approach Fails:**

1. **If Backend Performance Issues:**
   - Fall back to Approach B (client-side aggregation)
   - Make multiple API calls to existing endpoints
   - Aggregate data in frontend

2. **If Frontend Complexity Issues:**
   - Simplify table to basic HTML table
   - Remove advanced features (filtering, sorting)
   - Focus on data display only

---

## ESTIMATED EFFORT SUMMARY

- **Phase 1 (Backend):** 5-8 hours
- **Phase 2 (Frontend):** 10-15 hours
- **Phase 3 (Integration):** 3-4 hours
- **Phase 4 (Testing):** 6-9 hours
- **Total:** 24-36 hours

---

## DEPENDENCIES

- **E4-005 (EVM Aggregation Logic):** ✅ Complete - provides EVM metrics
- **E4-006 (EVM Summary Displays):** ✅ Complete - provides formatting helpers
- **E4-011 (Time Machine Control):** ✅ Complete - provides control date integration
- **E4-010 (Report Export):** ⏸️ Not needed for MVP - can be added later

---

## NOTES

- **Performance:** With 30-40 WBEs and up to 200 cost elements, client-side rendering should be sufficient. No pagination needed for MVP.
- **Filtering:** Start with client-side filtering (WBE, department). Architecture designed to support server-side filtering extension.
- **Period Performance:** Data structure designed to support 1-year period performance addition in future enhancement.
- **Export:** Export functionality deferred to E4-010. Component structure designed to support export integration.

---

**Plan Code:** E4-007-918277
**Plan Date:** 2025-11-17
**Plan Time:** 06:51 CET (Europe/Rome)
**Status:** Ready for Implementation
