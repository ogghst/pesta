# High-Level Analysis: E4-007 Cost Performance Report

**Task:** E4-007 - Cost Performance Report
**Sprint:** Sprint 5 - Reporting and Performance Dashboards
**Status:** Analysis Phase
**Date:** 2025-11-17
**Current Time:** 06:43 CET (Europe/Rome)

---

## User Story

As a project manager analyzing project performance,
I want to view a comprehensive Cost Performance Report showing cumulative and period performance with all key EVM metrics in a tabular format,
So that I can assess project health, identify performance trends, and make informed decisions about resource allocation and corrective actions.

---

## 1. CODEBASE PATTERN ANALYSIS

### 1.1 Existing Table Display Components

1. **DataTable Component – E1-007**
   - **Location:** `frontend/src/components/DataTable/DataTable.tsx`
   - **Architecture Layers:**
     - TanStack Table v8 (`@tanstack/react-table`) for table logic
     - Chakra UI (`Table.Root`, `Table.Header`, `Table.Body`) for styling
     - Column definitions with `ColumnDefExtended` type
     - Features: sorting, filtering, column resizing, column visibility toggle, pagination
     - Row click handlers for navigation
     - Loading states with skeleton components
   - **Patterns to respect:**
     - TypeScript generics for type-safe data (`DataTable<TData>`)
     - Manual pagination via URL search params
     - Client-side filtering and sorting
     - Responsive design with mobile optimization
     - Consistent column definition structure

2. **Hierarchical Table Patterns**
   - **BaselineCostElementsByWBETable – E3-008**
     - **Location:** `frontend/src/components/Projects/BaselineCostElementsByWBETable.tsx`
     - **Pattern:** Collapsible accordion sections grouped by WBE
     - **Architecture:** Chakra UI `Collapsible` with nested table rows
     - **Use Case:** Shows hierarchical data (WBE → Cost Elements) with drill-down capability
   - **Patterns to respect:**
     - Grouped display with summary totals at parent level
     - Expandable/collapsible sections for hierarchical navigation
     - Summary metrics displayed at each hierarchy level

3. **Project/WBE/Cost Element Tables**
   - **Location:** `frontend/src/routes/_layout/projects.$id.tsx`, `projects.$id.wbes.$wbeId.tsx`
   - **Pattern:** Flat table with row click navigation to detail pages
   - **Features:** Pagination, sorting, filtering, column visibility
   - **Integration:** Uses `DataTable` component with TanStack Table

### 1.2 Existing EVM Metrics Display Components

1. **EarnedValueSummary Component – E4-006**
   - **Location:** `frontend/src/components/Projects/EarnedValueSummary.tsx`
   - **Architecture Layers:**
     - React Query (`useQuery`) for data fetching
     - `EvmMetricsService` for API calls
     - Time-machine integration via `useTimeMachine()` hook
     - Metric cards with color-coded status indicators
     - Supports project, WBE, and cost-element levels
   - **Data Provided:**
     - Core metrics: `planned_value`, `earned_value`, `actual_cost`, `budget_bac`
     - Performance indices: `cpi`, `spi`, `tcpi` (can be `None` or `"overrun"`)
     - Variances: `cost_variance`, `schedule_variance`
   - **Patterns to respect:**
     - Level-based props (`level: "project" | "wbe" | "cost-element"`)
     - Control date integration for time-machine functionality
     - Formatting helpers (currency, percentage, decimals)
     - Status indicator logic with color thresholds

2. **MetricsSummary Component – Integration Pattern**
   - **Location:** `frontend/src/components/Projects/MetricsSummary.tsx`
   - **Architecture:** Container component composing multiple summary components
   - **Pattern:** Composition pattern for combining BudgetSummary, CostSummary, EarnedValueSummary
   - **Integration:** Used in project, WBE, and cost element detail pages

### 1.3 Backend API Patterns

1. **Unified EVM Metrics Endpoints – E4-005**
   - **Location:** `backend/app/api/routes/evm_aggregation.py`
   - **Endpoints:**
     - `GET /projects/{project_id}/evm-metrics/cost-elements/{cost_element_id}`
     - `GET /projects/{project_id}/evm-metrics/wbes/{wbe_id}`
     - `GET /projects/{project_id}/evm-metrics`
   - **Response Models:**
     - `EVMIndicesCostElementPublic`
     - `EVMIndicesWBEPublic`
     - `EVMIndicesProjectPublic`
   - **Data Provided:**
     - All EVM metrics: PV, EV, AC, BAC, CPI, SPI, TCPI, CV, SV
     - Time-machine control date dependency injection
   - **Patterns to respect:**
     - Hierarchical aggregation (cost element → WBE → project)
     - Single endpoint providing all metrics
     - TypeScript types already generated

2. **Report Generation Patterns (Not Yet Implemented)**
   - **Current State:** No dedicated report endpoints exist
   - **Expected Pattern:** Based on PRD requirements, reports should support:
     - Project, WBE, and cost element levels
     - Drill-down capabilities
     - Cumulative and period performance views
     - Export functionality (CSV, Excel) - E4-010

### 1.4 Architectural Layers to Respect

- **Frontend Component Layer:** React components using Chakra UI and TanStack Table
- **Data Fetching Layer:** React Query (`useQuery`) with service-based API calls
- **API Layer:** FastAPI routes with dependency injection, time-machine control date
- **Service Layer:** Pure calculation functions with no DB access
- **Models Layer:** Response schemas following Base/Create/Update/Public pattern
- **Time-Machine Integration:** All data must respect control date via `useTimeMachine()` hook

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### 2.1 Backend Modules Requiring Modification

1. **New Cost Performance Report API Endpoint (Proposed)**
   - **Candidate:** `backend/app/api/routes/cost_performance_report.py` OR extend `evm_aggregation.py`
   - **Endpoints:**
     - `GET /projects/{project_id}/reports/cost-performance` (project level)
     - `GET /projects/{project_id}/reports/cost-performance/wbes/{wbe_id}` (WBE level - optional)
     - `GET /projects/{project_id}/reports/cost-performance/cost-elements/{cost_element_id}` (cost element level - optional)
   - **Response Model:**
     - `CostPerformanceReportPublic` - Array of report rows with all EVM metrics
     - Each row represents a cost element (or aggregated WBE/project row)
   - **Dependencies:**
     - Reuse existing `EvmMetricsService` aggregation logic
     - `SessionDep`, `CurrentUser`, `get_time_machine_control_date`
     - Optional: date range filtering for period performance (future enhancement)
   - **Data Structure:**
     - Flat array of rows with hierarchical metadata (project_id, wbe_id, cost_element_id)
     - Include parent-child relationships for drill-down navigation
     - Cumulative metrics (total PV, EV, AC, BAC, CPI, SPI, TCPI, CV, SV)
     - Optional: Period metrics (period PV, EV, AC) - future enhancement

2. **Service Layer (No Changes Required)**
   - **Existing Services:** `evm_aggregation.py` already provides all required metrics
   - **Reuse:** `get_cost_element_evm_metrics()`, `get_wbe_evm_metrics()`, `get_project_evm_metrics()`
   - **Note:** Report endpoint will aggregate existing service calls, no new calculation logic needed

### 2.2 Frontend Components Requiring Modification

1. **New CostPerformanceReport Component (Proposed)**
   - **Candidate:** `frontend/src/components/Reports/CostPerformanceReport.tsx`
   - **Architecture:**
     - Uses `DataTable` component with TanStack Table
     - React Query for data fetching
     - Time-machine integration via `useTimeMachine()` hook
     - Level-based props (`level: "project" | "wbe" | "cost-element"`)
   - **Features:**
     - Tabular display with all EVM metrics as columns
     - Sorting by any column
     - Filtering by WBE, department, cost element type
     - Row click navigation to detail pages (drill-down)
     - Color-coded status indicators for CPI, SPI, CV, SV
     - Summary row(s) showing aggregated totals
   - **Column Definitions:**
     - Hierarchy columns: WBE (machine_type), Cost Element (department_code, department_name)
     - Core metrics: BAC, PV, EV, AC
     - Performance indices: CPI, SPI, TCPI
     - Variances: CV, SV
     - Percent complete: EV/BAC, PV/BAC
     - Status indicators: Color-coded cells for indices and variances

2. **Report Page Integration (Proposed)**
   - **Candidate:** `frontend/src/routes/_layout/projects.$id.reports.cost-performance.tsx`
   - **Architecture:**
     - New route for dedicated report page
     - Tabbed layout (if multiple reports exist) or standalone page
     - Integration with project detail page via navigation
   - **Features:**
     - Report header with project name, control date, report generation timestamp
     - Filter controls (WBE selection, date range - future)
     - Export buttons (CSV, Excel) - E4-010 integration
     - Print-friendly styling option

3. **Navigation Integration**
   - **Project Detail Page:** Add "Reports" tab or link to cost performance report
   - **WBE Detail Page:** Optional link to WBE-level report
   - **Cost Element Detail Page:** Optional link to cost element-level report

### 2.3 System Dependencies and External Integrations

- **Database:** No schema changes required; report uses existing EVM aggregation data
- **Time-Machine:** All report data must respect control date via `get_time_machine_control_date` dependency
- **Export Functionality:** Integration with E4-010 (Report Export) for CSV/Excel export
- **Frontend Libraries:**
  - TanStack Table (already in use) - for table display
  - React Query (already in use) - for data fetching
  - Chakra UI (already in use) - for UI components
  - **New Dependencies (for E4-010):**
    - CSV export: `export-to-csv` or `react-csv` (lightweight, zero dependencies)
    - Excel export: `exceljs` or `xlsx` (comprehensive Excel support)

### 2.4 Configuration Patterns

- Reuse existing time-machine control date injection
- Reuse existing API versioning (`/api/v1/projects/{project_id}/...`)
- Follow existing route patterns (`/projects/$id/reports/cost-performance`)
- Reuse existing formatting helpers (currency, percentage, decimals) from `EarnedValueSummary`

---

## 3. ABSTRACTION INVENTORY

### 3.1 Existing Abstractions to Leverage

1. **DataTable Component**
   - **Location:** `frontend/src/components/DataTable/DataTable.tsx`
   - **Reuse:** Complete table component with sorting, filtering, pagination, column visibility
   - **Extension:** Add report-specific features (summary rows, color-coded cells, export buttons)

2. **EVM Metrics Service**
   - **Location:** `frontend/src/client/sdk.gen.ts` - `EvmMetricsService`
   - **Reuse:** Existing API client methods for fetching EVM metrics
   - **Extension:** New report endpoint will provide aggregated data for multiple cost elements

3. **Formatting Helpers**
   - **Location:** `frontend/src/components/Projects/EarnedValueSummary.tsx`
   - **Functions:**
     - `formatCurrency()` - Currency formatting with EUR symbol
     - `formatPercent()` - Percentage formatting
     - `formatIndex()` - Decimal formatting for CPI/SPI/TCPI
   - **Reuse:** Extract to shared utility or reuse directly

4. **Status Indicator Helpers**
   - **Location:** `frontend/src/components/Projects/EarnedValueSummary.tsx`
   - **Functions:**
     - `getCpiStatus()`, `getSpiStatus()`, `getTcpiStatus()`, `getCvStatus()`, `getSvStatus()`
   - **Reuse:** Extract to shared utility for consistent color coding across components

5. **Time-Machine Hook**
   - **Location:** `frontend/src/hooks/useTimeMachine.ts` (assumed)
   - **Reuse:** `useTimeMachine()` hook for control date integration
   - **Pattern:** All report queries must include control date in query key

6. **Column Definition Pattern**
   - **Location:** `frontend/src/routes/_layout/projects.$id.tsx` (wbesColumns example)
   - **Pattern:** `ColumnDefExtended<TData>[]` with accessor functions, header, cell renderers
   - **Reuse:** Follow same pattern for report columns

### 3.2 Test Utilities and Fixtures

1. **Backend Test Patterns**
   - **Location:** `backend/tests/api/routes/test_evm_indices.py`, `test_evm_aggregation.py`
   - **Patterns:**
     - Fixture-based test data creation (projects, WBEs, cost elements)
     - Time-machine control date testing
     - Aggregation validation tests
   - **Reuse:** Similar test structure for report endpoint

2. **Frontend Test Patterns**
   - **Location:** `frontend/tests/` (Playwright E2E tests)
   - **Pattern:** Component testing with mocked API responses
   - **Reuse:** Similar test structure for report component

### 3.3 Dependency Injection Patterns

- **Backend:** FastAPI dependency injection (`Depends`) for session, user, control date
- **Frontend:** React Query for data fetching with automatic caching and refetching
- **Service Location:** OpenAPI-generated client services (`EvmMetricsService`, etc.)

---

## 4. ALTERNATIVE APPROACHES

### Approach A – Dedicated Report Component with New API Endpoint (Recommended)

- **Summary:** Create a new `CostPerformanceReport` component with a dedicated backend API endpoint that returns a flat array of report rows (cost elements with aggregated WBE/project rows).

- **Backend:**
  - New endpoint: `GET /projects/{project_id}/reports/cost-performance`
  - Returns array of rows, each containing all EVM metrics
  - Includes hierarchical metadata (wbe_id, cost_element_id) for drill-down
  - Reuses existing `EvmMetricsService` aggregation logic

- **Frontend:**
  - New component: `CostPerformanceReport.tsx`
  - Uses `DataTable` component with TanStack Table
  - Column definitions for all EVM metrics
  - Color-coded status indicators
  - Row click navigation for drill-down
  - Summary rows for aggregated totals

- **Pros:**
  - Clear separation of concerns (dedicated report endpoint)
  - Optimized for report use case (single API call for all data)
  - Easy to extend with period performance, filtering, export
  - Follows established patterns (DataTable, EvmMetricsService)
  - Can be reused by E4-008 (Variance Analysis Report) and E4-009 (Dashboard)

- **Cons/Risks:**
  - Requires new backend endpoint (but reuses existing services)
  - May need pagination for large projects (many cost elements)
  - Initial implementation complexity (but follows established patterns)

- **Architectural Alignment:** High – follows established patterns, respects component composition, maintains consistency

- **Estimated Complexity:** Medium – 15-20 hours (backend 4-6h, frontend 8-12h, testing 3-4h)

- **Risk Factors:**
  - Performance with large datasets (many cost elements) - may need pagination or server-side filtering
  - Export functionality (E4-010) requires additional libraries and implementation

### Approach B – Client-Side Aggregation Using Existing Endpoints

- **Summary:** Build report component that makes multiple API calls to existing EVM metrics endpoints and aggregates data client-side.

- **Backend:**
  - No new endpoints required
  - Reuse existing `EvmMetricsService` endpoints

- **Frontend:**
  - New component: `CostPerformanceReport.tsx`
  - Multiple `useQuery` calls to fetch EVM metrics for all cost elements
  - Client-side aggregation and table rendering
  - Uses `DataTable` component

- **Pros:**
  - No backend changes required
  - Faster initial implementation
  - Leverages existing API endpoints

- **Cons/Risks:**
  - Multiple API calls (N+1 problem for cost elements)
  - Client-side performance issues with large datasets
  - Network overhead (many HTTP requests)
  - Inconsistent with report generation patterns (reports typically server-generated)
  - Difficult to add period performance or advanced filtering

- **Architectural Alignment:** Medium – works but not optimal for report use case

- **Estimated Complexity:** Low-Medium – 10-15 hours (frontend only, but more complex client-side logic)

- **Risk Factors:**
  - Performance degradation with many cost elements
  - Network latency with multiple API calls
  - Client-side memory usage for large datasets

### Approach C – Hybrid: Server-Generated Report with Client-Side Enhancements

- **Summary:** Backend generates report data structure optimized for tabular display, frontend adds interactive features (sorting, filtering, export).

- **Backend:**
  - New endpoint: `GET /projects/{project_id}/reports/cost-performance`
  - Returns structured report data (rows + metadata)
  - Includes pre-computed aggregations and summary rows
  - Optional: Server-side filtering and sorting parameters

- **Frontend:**
  - New component: `CostPerformanceReport.tsx`
  - Single API call for report data
  - Client-side sorting, filtering, column visibility (TanStack Table)
  - Export functionality (CSV, Excel) - E4-010

- **Pros:**
  - Optimized data structure for report display
  - Single API call (better performance)
  - Server-side aggregation (consistent with report patterns)
  - Client-side interactivity (sorting, filtering, export)
  - Can add server-side filtering later for large datasets

- **Cons/Risks:**
  - Requires new backend endpoint
  - More complex backend logic (but reuses existing services)
  - Initial implementation complexity

- **Architectural Alignment:** High – optimal for report use case, balances server/client responsibilities

- **Estimated Complexity:** Medium-High – 18-24 hours (backend 6-8h, frontend 10-14h, testing 2-3h)

- **Risk Factors:**
  - Backend complexity for report data structure
  - Performance with large datasets (may need pagination)

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### 5.1 Architectural Principles

- **Single Responsibility:** ✅ Report component dedicated to cost performance reporting
- **DRY (Don't Repeat Yourself):** ✅ Reuses existing EVM aggregation services, formatting helpers, DataTable component
- **Separation of Concerns:** ✅ Backend handles data aggregation, frontend handles presentation and interactivity
- **Consistency:** ✅ Follows established patterns (DataTable, EvmMetricsService, time-machine integration)

### 5.2 Future Maintenance Burden

- **Positive Impacts:**
  - Reuses existing services and components (less code to maintain)
  - Follows established patterns (easier for team to understand)
  - Clear separation of report logic (easy to extend with new reports)

- **Potential Concerns:**
  - Report-specific endpoint may need updates if EVM calculation logic changes
  - Export functionality (E4-010) adds dependency on external libraries
  - Large datasets may require pagination or server-side filtering (future enhancement)

### 5.3 Testing Challenges

- **Backend Testing:**
  - Test report endpoint with various project structures (single WBE, multiple WBEs, many cost elements)
  - Validate aggregation accuracy (compare with individual EVM metrics)
  - Test time-machine control date filtering
  - Test edge cases (no data, single cost element, large datasets)

- **Frontend Testing:**
  - Test table rendering with various data sizes
  - Test sorting, filtering, column visibility
  - Test row click navigation (drill-down)
  - Test color-coded status indicators
  - Test export functionality (E4-010)
  - Test time-machine integration
  - Test responsive design (mobile, tablet, desktop)

- **Integration Testing:**
  - End-to-end test: Generate report, verify data accuracy, test export
  - Test drill-down navigation from report to detail pages
  - Test report with different control dates (time-machine)

### 5.4 Performance Considerations

- **Backend:**
  - Single API call for all report data (better than multiple calls)
  - Reuses existing aggregation services (no duplicate calculations)
  - Potential bottleneck: Large projects with many cost elements (may need pagination)

- **Frontend:**
  - TanStack Table handles large datasets efficiently (virtualization not needed for typical project sizes)
  - Client-side sorting/filtering is fast for typical dataset sizes (< 1000 rows)
  - Export functionality may be slow for very large datasets (consider async export or progress indicator)

### 5.5 Scalability Considerations

- **Current MVP Scope:** Reports for single project with typical size (< 50 WBEs, < 500 cost elements)
- **Future Enhancements:**
  - Server-side pagination for large projects
  - Server-side filtering and sorting
  - Caching of report data
  - Background report generation for very large projects
  - Report scheduling and email delivery

---

## SUMMARY & RECOMMENDATIONS

### User Story Summary

**What:** Create a Cost Performance Report component that displays cumulative EVM performance metrics (PV, EV, AC, BAC, CPI, SPI, TCPI, CV, SV) in a tabular format at project, WBE, and cost element levels, with drill-down capabilities and export functionality.

**Why:** Provide project managers with a comprehensive view of project performance in a standardized report format, enabling quick identification of performance issues, trend analysis, and data-driven decision-making. Supports compliance with EVM reporting requirements and facilitates communication with stakeholders.

### Recommended Approach

**Approach A – Dedicated Report Component with New API Endpoint** is recommended because:

1. **Optimal Performance:** Single API call for all report data (better than multiple calls)
2. **Scalability:** Can add server-side filtering, pagination, and caching for large datasets
3. **Consistency:** Follows established report generation patterns (server-generated, client-enhanced)
4. **Extensibility:** Easy to extend with period performance, advanced filtering, and other report types
5. **Maintainability:** Clear separation of concerns, reuses existing services and components

### Business Rules Confirmed

- **Report Levels:** Project, WBE, and cost element levels (per PRD 13.1)
- **Metrics Included:** All key EVM metrics (PV, EV, AC, BAC, CPI, SPI, TCPI, CV, SV)
- **Format:** Tabular format with cumulative performance (period performance - future enhancement)
- **Drill-Down:** Row click navigation to detail pages (project → WBE → cost element)
- **Export:** CSV and Excel export (E4-010 integration)
- **Time-Machine:** All metrics respect control date via time-machine integration

### Implementation Scope

- **Backend:**
  - New API endpoint: `GET /projects/{project_id}/reports/cost-performance`
  - Response model: `CostPerformanceReportPublic` (array of report rows)
  - Reuses existing `EvmMetricsService` aggregation logic
  - Estimated: 4-6 hours

- **Frontend:**
  - New component: `CostPerformanceReport.tsx`
  - New route: `/projects/$id/reports/cost-performance`
  - Uses `DataTable` component with TanStack Table
  - Column definitions for all EVM metrics
  - Color-coded status indicators
  - Row click navigation (drill-down)
  - Summary rows for aggregated totals
  - Estimated: 8-12 hours

- **Testing:**
  - Backend API tests (aggregation accuracy, edge cases)
  - Frontend component tests (rendering, interactivity)
  - Integration tests (end-to-end report generation)
  - Estimated: 3-4 hours

- **Total Estimated Effort:** 15-22 hours

### Risks and Unknowns

1. **Performance with Large Datasets:**
   - **Risk:** Projects with many cost elements (> 500) may cause slow report generation
   - **Mitigation:** Start with client-side rendering, add server-side pagination if needed
   - **Unknown:** Typical project size in production (need stakeholder input)

2. **Export Functionality (E4-010):**
   - **Risk:** Export libraries may have compatibility issues or performance problems
   - **Mitigation:** Research and test export libraries before implementation
   - **Unknown:** Preferred export format (CSV vs Excel) and file size limits

3. **Period Performance:**
   - **Risk:** PRD mentions "cumulative and period performance" but period logic not yet defined
   - **Mitigation:** Implement cumulative performance first, add period performance in future enhancement
   - **Unknown:** Period definition (monthly, quarterly, custom date ranges)

4. **Report Filtering:**
   - **Risk:** Users may want to filter by WBE, department, cost element type
   - **Mitigation:** Start with basic filtering (client-side), add server-side filtering if needed
   - **Unknown:** Required filter options (need stakeholder input)

### Dependencies

- **E4-005 (EVM Aggregation Logic):** ✅ Complete - provides all required EVM metrics
- **E4-006 (EVM Summary Displays):** ✅ Complete - provides formatting helpers and status indicators
- **E4-010 (Report Export Functionality):** ⏳ Todo - required for CSV/Excel export
- **E4-011 (Time Machine Control):** ✅ Complete - required for control date integration

### Next Steps

1. **Stakeholder Clarification:**
   - Confirm typical project size (number of WBEs, cost elements)
   - Confirm required filter options
   - Confirm period performance definition (if needed in MVP)
   - Confirm export format preferences (CSV vs Excel)

2. **Library Research:**
   - Evaluate CSV export libraries (`export-to-csv`, `react-csv`)
   - Evaluate Excel export libraries (`exceljs`, `xlsx`)
   - Test performance with sample datasets

3. **Detailed Planning:**
   - Create detailed TDD implementation plan
   - Define API response model structure
   - Define frontend component structure and column definitions
   - Plan test coverage (backend, frontend, integration)

---

**Analysis Code:** E4-007-918277
**Analysis Date:** 2025-11-17
**Analysis Time:** 06:43 CET (Europe/Rome)
**Status:** Ready for Review and Detailed Planning Phase
