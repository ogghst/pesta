# High-Level Analysis: Baseline Snapshot View UI Component

## Objective
Create a UI component to view baseline snapshot data for a selected baseline, displaying:
1. **Overall project values** (aggregated summary)
2. **Table showing BaselineCostElement per WBE** (grouped by WBE)
3. **Table showing all BaselineCostElement records** (flat list)

---

## 1. CODEBASE PATTERN ANALYSIS

### Similar Implementations Found

#### Pattern 1: Summary Components with Aggregated Values
**Files:**
- `frontend/src/components/Projects/BudgetSummary.tsx`
- `frontend/src/components/Projects/CostSummary.tsx`

**Pattern:**
- Uses `Grid` layout with `Box` components for metric cards
- Fetches aggregated data via TanStack Query (`useQuery`)
- Displays summary cards with formatted currency values
- Uses `VStack` for card content organization
- Loading states with `SkeletonText` placeholders
- Responsive grid: `base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(4, 1fr)"`

**Key Interfaces:**
- `BudgetSummaryPublic` / `CostSummaryPublic` schemas from backend
- Service methods: `BudgetSummaryService.getProjectBudgetSummary()`, `CostSummaryService.getProjectCostSummary()`
- Props pattern: `level: "project" | "wbe" | "cost-element"` with corresponding ID

#### Pattern 2: Modal Dialogs for Detail Views
**Files:**
- `frontend/src/components/Projects/EditCostRegistration.tsx`
- `frontend/src/components/Projects/EditBaselineLog.tsx`

**Pattern:**
- Uses `DialogRoot` / `DialogContent` from `@/components/ui/dialog`
- Controlled open state: `useState(false)` with `isOpen`
- `DialogTrigger` wraps button/action to open modal
- Fetches data when modal opens: `enabled: isOpen` in `useQuery`
- Loading states handled within modal content
- Size: `size={{ base: "xs", md: "lg" }}`

**Key Components:**
- `DialogHeader`, `DialogTitle`, `DialogBody`, `DialogFooter`
- `DialogActionTrigger` for cancel buttons
- Form management with React Hook Form (for edit modals)

#### Pattern 3: Data Tables with Grouping
**Files:**
- `frontend/src/components/Projects/BaselineLogsTable.tsx`
- `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.tsx` (CostElementsTable)

**Pattern:**
- Uses `DataTable` component from `@/components/DataTable/DataTable`
- Column definitions: `ColumnDefExtended<TData>[]`
- TanStack Table for sorting, filtering, resizing
- Pagination handled via URL search params (for paginated tables)
- Action buttons in table cells (Edit, Delete, etc.)

**Key Abstractions:**
- `DataTable` component with props: `data`, `columns`, `tableId`, `isLoading`, `count`, `page`, `onPageChange`, `pageSize`
- `ColumnDefExtended` type from `@/components/DataTable/types`

### Established Architectural Layers

1. **API Layer (Backend):**
   - FastAPI routers in `backend/app/api/routes/`
   - Service methods return Pydantic models (e.g., `BaselineLogPublic`)
   - Aggregation logic in route handlers (e.g., `cost_summary.py`, `budget_summary.py`)

2. **Client Layer (Frontend):**
   - Auto-generated TypeScript client (`frontend/src/client/`)
   - Service classes: `BaselineLogsService`, `CostSummaryService`, etc.
   - Types: `BaselineLogPublic`, `BaselineCostElementPublic`, etc.

3. **UI Component Layer:**
   - Chakra UI components (`@chakra-ui/react`)
   - Custom UI components (`@/components/ui/`)
   - DataTable abstraction for consistent table rendering

4. **State Management:**
   - TanStack Query for server state
   - React Hook Form for form state
   - Local state (`useState`) for UI state (modal open/close)

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### Backend API Endpoints (New/Modified)

#### Required New Endpoints:

1. **`GET /api/v1/projects/{project_id}/baseline-logs/{baseline_id}/snapshot`**
   - **Purpose:** Fetch baseline snapshot data with aggregated project values
   - **Returns:**
     - `BaselineSnapshotPublic` (snapshot metadata)
     - Aggregated totals: `total_budget_bac`, `total_revenue_plan`, `total_actual_ac`, `total_forecast_eac`, `total_earned_ev`
   - **Location:** `backend/app/api/routes/baseline_logs.py`
   - **Dependencies:**
     - `BaselineSnapshot` model (already exists)
     - `BaselineCostElement` model (already exists)
     - SQLModel aggregation queries

2. **`GET /api/v1/projects/{project_id}/baseline-logs/{baseline_id}/cost-elements-by-wbe`**
   - **Purpose:** Fetch BaselineCostElement records grouped by WBE
   - **Returns:**
     - List of objects with:
       - `wbe_id`, `wbe_machine_type` (WBE info)
       - `cost_elements`: List of `BaselineCostElementPublic` with `CostElement` info (department, type, etc.)
       - Aggregated WBE totals
   - **Location:** `backend/app/api/routes/baseline_logs.py`
   - **Dependencies:**
     - Join: `BaselineCostElement` → `CostElement` → `WBE`
     - Grouping logic by `WBE.wbe_id`

3. **`GET /api/v1/projects/{project_id}/baseline-logs/{baseline_id}/cost-elements`**
   - **Purpose:** Fetch all BaselineCostElement records for a baseline (flat list)
   - **Returns:**
     - `BaselineCostElementsPublic` with pagination: `{ data: BaselineCostElementPublic[], count: int }`
     - Includes related `CostElement` info (department_code, department_name, cost_element_type, etc.)
   - **Location:** `backend/app/api/routes/baseline_logs.py`
   - **Dependencies:**
     - Join: `BaselineCostElement` → `CostElement` (for display fields)
     - Optional pagination (skip/limit)

**Files to Modify:**
- `backend/app/api/routes/baseline_logs.py` - Add new endpoints
- `backend/app/models/baseline_cost_element.py` - Add response schemas (if needed)
- `backend/tests/api/routes/test_baseline_logs.py` - Add tests for new endpoints

### Frontend Components (New)

#### Required New Components:

1. **`ViewBaselineSnapshot.tsx`** (Modal Component)
   - **Location:** `frontend/src/components/Projects/ViewBaselineSnapshot.tsx`
   - **Purpose:** Main modal component that orchestrates the view
   - **Props:** `baselineId: string`, `projectId: string`
   - **Structure:**
     - Modal with tabs or sections:
       - Section 1: Overall Project Values (summary cards)
       - Section 2: BaselineCostElement by WBE (grouped table)
       - Section 3: All BaselineCostElement Records (flat table)
   - **Dependencies:**
     - `DialogRoot` / `DialogContent` from `@/components/ui/dialog`
     - `BaselineSnapshotSummary` component (summary cards)
     - `BaselineCostElementsByWBETable` component (grouped table)
     - `BaselineCostElementsTable` component (flat table)

2. **`BaselineSnapshotSummary.tsx`** (Summary Cards)
   - **Location:** `frontend/src/components/Projects/BaselineSnapshotSummary.tsx`
   - **Purpose:** Display aggregated project values
   - **Pattern:** Similar to `BudgetSummary` / `CostSummary` components
   - **Dependencies:**
     - `Grid`, `Box`, `VStack`, `Text` from Chakra UI
     - API endpoint: `GET /baseline-logs/{baseline_id}/snapshot`

3. **`BaselineCostElementsByWBETable.tsx`** (Grouped Table)
   - **Location:** `frontend/src/components/Projects/BaselineCostElementsByWBETable.tsx`
   - **Purpose:** Display BaselineCostElement records grouped by WBE
   - **Pattern:** Similar to how cost elements are displayed in WBE detail pages
   - **Structure:**
     - Accordion or expandable sections per WBE
     - Each section shows: WBE name, aggregated totals for that WBE
     - Nested table of BaselineCostElement records for that WBE
   - **Dependencies:**
     - `DataTable` component (for nested tables)
     - `Accordion` or `Collapsible` from Chakra UI (for grouping)
     - API endpoint: `GET /baseline-logs/{baseline_id}/cost-elements-by-wbe`

4. **`BaselineCostElementsTable.tsx`** (Flat Table)
   - **Location:** `frontend/src/components/Projects/BaselineCostElementsTable.tsx`
   - **Purpose:** Display all BaselineCostElement records in a flat table
   - **Pattern:** Similar to `CostRegistrationsTable` or `BaselineLogsTable`
   - **Columns:**
     - WBE (machine_type), Cost Element (department/code), Budget BAC, Revenue Plan, Actual AC, Forecast EAC, Earned EV
   - **Dependencies:**
     - `DataTable` component
     - API endpoint: `GET /baseline-logs/{baseline_id}/cost-elements`

**Files to Modify:**
- `frontend/src/components/Projects/BaselineLogsTable.tsx` - Add "View" button in actions column
- `frontend/src/client/sdk.gen.ts` - Will be regenerated after API changes
- `frontend/src/client/types.gen.ts` - Will be regenerated with new schemas

### Configuration Patterns

- **API Base URL:** Defined in `frontend/src/client/core/OpenAPI.ts` (auto-generated)
- **Query Keys:** Follow pattern: `["baseline-snapshot", { projectId, baselineId }]`
- **Error Handling:** Uses `handleError` utility from `@/utils`
- **Toast Notifications:** Uses `useCustomToast` hook for success/error messages

---

## 3. ABSTRACTION INVENTORY

### Existing Abstractions to Leverage

1. **DataTable Component**
   - **Location:** `frontend/src/components/DataTable/DataTable.tsx`
   - **Usage:** For both grouped and flat tables
   - **Features:** Sorting, filtering, resizing, pagination
   - **Type:** `ColumnDefExtended<TData>[]` for column definitions

2. **Dialog/Modal Pattern**
   - **Location:** `frontend/src/components/ui/dialog.tsx`
   - **Components:** `DialogRoot`, `DialogContent`, `DialogHeader`, `DialogBody`, `DialogFooter`, `DialogTrigger`
   - **Usage:** Standard modal pattern for detail views

3. **Summary Card Pattern**
   - **Pattern:** `Grid` with `Box` components (from `BudgetSummary` / `CostSummary`)
   - **Formatting:** Currency formatting utilities (can reuse from `CostSummary.tsx`)

4. **TanStack Query Patterns**
   - **Query hooks:** `useQuery` for data fetching
   - **Query keys:** Consistent naming: `["resource", { params }]`
   - **Loading states:** `isLoading` prop passed to components

5. **Type System**
   - **Auto-generated types:** `BaselineCostElementPublic`, `BaselineSnapshotPublic`
   - **Service methods:** `BaselineLogsService.*` (to be extended)

### Test Utilities

- **Backend:** `backend/tests/conftest.py` - Database fixtures, `db` session fixture
- **Frontend:** Test utilities for React Query (if needed)

### Utility Functions

- **Currency formatting:** `formatCurrency` function in `CostSummary.tsx` (can be extracted to shared utility)
- **Date formatting:** `toLocaleDateString()` pattern used in table cells
- **Error handling:** `handleError` from `@/utils`

---

## 4. ALTERNATIVE APPROACHES

### Approach 1: Modal Dialog with Tabs (Recommended)

**Structure:**
- Single modal (`ViewBaselineSnapshot`) with tabbed content:
  - Tab 1: "Summary" - Overall project values (cards)
  - Tab 2: "By WBE" - Grouped table by WBE
  - Tab 3: "All Cost Elements" - Flat table

**Pros:**
- ✅ Follows existing modal patterns (`EditBaselineLog`, `EditCostRegistration`)
- ✅ Clean separation of concerns (tabs for different views)
- ✅ Good UX (user can switch between views without closing modal)
- ✅ Consistent with existing UI patterns

**Cons:**
- ⚠️ Modal size may need to be large (`lg` or `xl`) for tables
- ⚠️ Multiple API calls (one per tab) or single call with all data

**Complexity:** Medium
**Risk:** Low (follows established patterns)

### Approach 2: Embedded View in Baseline Logs Table

**Structure:**
- Expandable rows in `BaselineLogsTable`
- Click row to expand and show snapshot data inline
- Or: Separate route/page: `/projects/{id}/baselines/{baselineId}`

**Pros:**
- ✅ No modal needed (embedded in table)
- ✅ Can use full page width for tables
- ✅ Better for large datasets

**Cons:**
- ⚠️ Deviates from existing patterns (no expandable rows in current tables)
- ⚠️ More complex state management (which row is expanded)
- ⚠️ If separate route: requires new route setup

**Complexity:** Medium-High
**Risk:** Medium (new pattern, more complex)

### Approach 3: Separate Page/Route

**Structure:**
- New route: `/projects/{id}/baselines/{baselineId}`
- Full page view with all three sections
- Navigation from BaselineLogsTable via "View" button

**Pros:**
- ✅ Maximum space for tables and data
- ✅ Better for printing/exporting
- ✅ Can bookmark specific baseline views
- ✅ URL-based navigation

**Cons:**
- ⚠️ Requires new route configuration
- ⚠️ More navigation (user leaves baselines table)
- ⚠️ Different from existing detail view patterns (WBEs use tabs, not separate routes)

**Complexity:** Medium
**Risk:** Low-Medium (requires routing setup)

### Approach 4: API Aggregation Strategy

**Option A: Single Endpoint with All Data**
- `GET /baseline-logs/{baseline_id}/snapshot-data`
- Returns: summary + grouped data + flat list (all in one response)

**Pros:**
- ✅ Single API call (better performance)
- ✅ Atomic data (all data from same snapshot)

**Cons:**
- ⚠️ Large response payload
- ⚠️ May fetch unused data (if user only views summary)

**Option B: Separate Endpoints per View**
- `GET /baseline-logs/{baseline_id}/snapshot` (summary)
- `GET /baseline-logs/{baseline_id}/cost-elements-by-wbe` (grouped)
- `GET /baseline-logs/{baseline_id}/cost-elements` (flat)

**Pros:**
- ✅ Smaller, focused responses
- ✅ Can lazy-load data (fetch on tab switch)
- ✅ Better caching (can cache summary separately)

**Cons:**
- ⚠️ Multiple API calls (if viewing all tabs)
- ⚠️ Potential inconsistency if data changes between calls

**Recommended:** Option B (separate endpoints) with lazy loading per tab

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### Architectural Principles Followed

1. **Separation of Concerns:**
   - ✅ Backend handles aggregation logic
   - ✅ Frontend handles presentation
   - ✅ Clear API contracts (Pydantic models)

2. **Reusability:**
   - ✅ Uses existing `DataTable` component
   - ✅ Reuses summary card pattern from `BudgetSummary` / `CostSummary`
   - ✅ Follows modal dialog pattern

3. **Consistency:**
   - ✅ Matches existing UI patterns (modals, tables, summary cards)
   - ✅ Follows naming conventions (`Baseline*` prefix)
   - ✅ Uses same state management (TanStack Query)

### Potential Maintenance Burden

1. **API Endpoint Complexity:**
   - ⚠️ Grouping by WBE requires join logic (BaselineCostElement → CostElement → WBE)
   - ⚠️ Aggregation calculations need to be tested and maintained
   - ✅ Mitigation: Reuse patterns from `cost_summary.py` / `budget_summary.py`

2. **Component Complexity:**
   - ⚠️ Modal with multiple tabs/sections may become large
   - ✅ Mitigation: Split into sub-components (Summary, ByWBETable, FlatTable)

3. **Data Consistency:**
   - ⚠️ Multiple endpoints may return slightly different aggregations (if data changes)
   - ✅ Mitigation: Use same baseline_id for all queries (snapshot is immutable)

4. **Performance:**
   - ⚠️ Large projects with many cost elements may have slow queries
   - ✅ Mitigation: Pagination for flat table, efficient SQL joins

### Testing Challenges

1. **Backend Tests:**
   - ✅ Can reuse test fixtures from `test_baseline_logs.py`
   - ⚠️ Need to test aggregation accuracy (sums, counts)
   - ⚠️ Need to test grouping logic (by WBE)

2. **Frontend Tests:**
   - ⚠️ Modal testing (open/close, tab switching)
   - ⚠️ Table rendering with grouped data
   - ⚠️ Loading states for multiple queries

3. **Integration Tests:**
   - ⚠️ End-to-end flow: Create baseline → View snapshot → Verify data
   - ✅ Can leverage existing test infrastructure

### Clarifications Received

1. **Data Volume:**
   - ✅ Max 30 baselines per project
   - ✅ Max 50 WBEs per project
   - ✅ With ~10-20 cost elements per WBE, max ~500-1000 cost elements per project
   - **Impact:** Flat table may need pagination (50-100 items per page), but summary and grouped views are manageable

2. **User Workflow:**
   - ✅ Hierarchical navigation: Project → WBE → Cost Elements
   - ✅ Users typically start at project level, drill down to WBE, then to cost elements
   - **Impact:** Grouped by WBE view aligns with user workflow (primary view), flat table is secondary

3. **Export/Print:**
   - ✅ No export/print functionality needed for baseline snapshot data

4. **Comparison Views:**
   - ✅ Baseline comparison is a planned feature (separate task)
   - **Impact:** Design snapshot view to be extensible for future comparison features

---

## Summary and Recommendations

### Recommended Approach
**Modal Dialog with Tabs + Separate API Endpoints (Lazy Loading)**

1. **UI Structure:**
   - Modal component (`ViewBaselineSnapshot`) opened from "View" button in BaselineLogsTable
   - Three tabs: Summary, By WBE, All Cost Elements
   - Size: `xl` to accommodate tables (max 50 WBEs, max ~1000 cost elements)
   - **Primary view:** "By WBE" tab (aligns with user workflow: Project → WBE → Cost Elements)
   - **Secondary view:** "All Cost Elements" tab (with pagination: 50-100 items per page)

2. **API Structure:**
   - Three separate endpoints (one per view)
   - Lazy load data when tab is activated
   - Cache queries per tab
   - **Pagination:** Flat table endpoint supports `skip`/`limit` (recommend 50-100 items per page)

3. **Components:**
   - `ViewBaselineSnapshot.tsx` (main modal with tabs)
   - `BaselineSnapshotSummary.tsx` (summary cards - 4 cards: Total Budget BAC, Total Revenue Plan, Total Actual AC, Total Forecast EAC, Total Earned EV)
   - `BaselineCostElementsByWBETable.tsx` (grouped table - accordion/collapsible sections per WBE)
   - `BaselineCostElementsTable.tsx` (flat table with pagination)

### Design Considerations (Based on Clarifications)

1. **Data Volume:**
   - Max 30 baselines per project → All can be displayed in BaselineLogsTable
   - Max 50 WBEs per project → Grouped view manageable (accordion/collapsible)
   - Max ~1000 cost elements per project → Flat table needs pagination (50-100 per page)

2. **User Workflow Alignment:**
   - **Primary:** "By WBE" tab (users start at project, drill to WBE, then cost elements)
   - **Secondary:** "All Cost Elements" tab (for comprehensive view/search)
   - **Summary:** Always visible (project-level overview)

3. **Extensibility:**
   - Design modal to support future baseline comparison (E3-009)
   - Consider modal size/positioning for side-by-side comparison (future)

### Next Steps
1. Create backend API endpoints (3 endpoints)
2. Generate TypeScript client
3. Create frontend components (4 components)
4. Add "View" button to BaselineLogsTable actions column
5. Test with real data (up to 50 WBEs, ~1000 cost elements)
