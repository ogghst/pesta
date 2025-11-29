# Cost Element Type Filtering for Project Performance Dashboard

**Analysis Code:** 483922
**Date:** 2025-01-27
**Feature:** Replace individual cost element selector with cost element type selector in ProjectPerformanceDashboard

## USER STORY

As a project manager, I want to filter the Project Performance Dashboard by cost element types instead of individual cost elements, so I can analyze performance metrics across all cost elements of the same type (e.g., all "Engineering" or all "Fabrication" cost elements) across one or multiple WBEs, enabling me to identify patterns and trends at a higher level of abstraction.

## 1. CODEBASE PATTERN ANALYSIS

### Existing Implementations

1. **BudgetTimelineFilter Component** (`frontend/src/components/Projects/BudgetTimelineFilter.tsx`)
   - **Pattern:** Uses collapsible sections with cost element type filtering
   - **Namespaces:** `CostElementTypesService` from `@/client`
   - **State Management:** `useState` for `selectedCostElementTypeIds`
   - **API:** `CostElementTypesService.readCostElementTypes()` - fetches all active types
   - **UI Pattern:** Badge-based selection with "Select All/Deselect All" buttons
   - **Filter Logic:** Filters cost elements by type IDs client-side before display

2. **Budget Timeline API** (`backend/app/api/routes/budget_timeline.py`)
   - **Endpoint:** `GET /projects/{project_id}/cost-elements-with-schedules`
   - **Filter Support:** Already supports `cost_element_type_ids` query parameter
   - **Implementation:** Server-side filtering at line 89-92 using SQL `WHERE CostElement.cost_element_type_id.in_(cost_element_type_ids)`
   - **Test Coverage:** `test_get_cost_elements_with_schedules_by_type` confirms functionality

3. **Cost Performance Report** (`backend/app/services/cost_performance_report.py`)
   - **Pattern:** Fetches cost element types as metadata for reporting
   - **Usage:** Builds lookup map of types for display purposes (line 139-151)
   - **Note:** Does not filter by type, but demonstrates type data access pattern

### Architectural Layers

- **Frontend:**
  - Service Layer: `CostElementTypesService` (auto-generated from OpenAPI)
  - Component Layer: Filter components using React Query (`useQuery`)
  - State Layer: Local component state with `useState`
  - UI Layer: Chakra UI `Collapsible`, `Badge`, `Checkbox` components

- **Backend:**
  - API Route Layer: FastAPI routes with Query parameters
  - Service Layer: SQLModel queries with type filtering
  - Model Layer: `CostElementType`, `CostElement` with relationship

## 2. INTEGRATION TOUCHPOINT MAPPING

### Files Requiring Modification

1. **`frontend/src/components/Reports/ProjectPerformanceDashboard.tsx`**
   - **Current State:** Uses `selectedCostElementIds` state and filters by individual cost element IDs
   - **Changes Required:**
     - Replace `selectedCostElementIds` with `selectedCostElementTypeIds`
     - Add `CostElementTypesService.readCostElementTypes()` query
     - Update `FiltersCard` to display cost element types instead of individual elements
     - Remove cost elements fetching/filtering logic (no longer needed for filter UI)
   - **Line References:**
     - Lines 49-51: `selectedCostElementIds` state declaration
     - Lines 59-60: Reset filters on project change
     - Lines 95-124: Cost elements query (can be simplified or removed)
     - Lines 165-169: `normalizedCostElementIds` memo
     - Lines 178-179: API call to `getCostElementsWithSchedules` with `costElementIds` parameter
     - Lines 233-234: `clearFilters` function
     - Lines 553-600: `drilldownItems` filtering logic
     - Lines 1035-1260: `FiltersCard` component with cost element checkboxes

2. **`frontend/src/components/Reports/ProjectPerformanceDashboard.tsx` - FiltersCard Component**
   - **Lines 1050-1260:** Replace cost element checkbox list with cost element type badge selector
   - **UI Pattern:** Follow `BudgetTimelineFilter` pattern (badges instead of checkboxes)
   - **Remove:** Cost elements prop and related display logic

3. **API Integration Points:**
   - **`BudgetTimelineService.getCostElementsWithSchedules`** (line 175-179)
     - **Current:** Accepts `costElementIds?: string[]`
     - **Change:** Replace with `costElementTypeIds?: string[]`
     - **Backend:** Already supports `cost_element_type_ids` parameter (verified)

   - **`ReportsService.getProjectVarianceAnalysisReportEndpoint`** (line 565-569)
     - **Current:** No type filtering support in API
     - **Change:** Client-side filtering of drilldown items by type (or no change if API doesn't support it)

4. **State Management:**
   - Replace `selectedCostElementIds` state throughout component
   - Update `normalizedCostElementIds` to `normalizedCostElementTypeIds`
   - Update query keys to include type IDs instead of element IDs

### Dependencies

- **External:**
  - `CostElementTypesService.readCostElementTypes()` - API service (already exists)
  - `BudgetTimelineService.getCostElementsWithSchedules()` - API service (supports type filtering)

- **Internal:**
  - Time Machine context for control date
  - React Query for data fetching
  - Chakra UI components for UI

### Configuration Patterns

- Cost element types are fetched globally (not project-specific)
- Only active types are displayed (`is_active: true`)
- Types are ordered by `display_order`
- No user-specific preferences for type filtering

## 3. ABSTRACTION INVENTORY

### Existing Abstractions to Leverage

1. **Service Pattern:**
   - `CostElementTypesService.readCostElementTypes()` - Standard service method
   - Returns `CostElementTypesPublic` with `data` and `count`
   - Type filtering pattern already established in `BudgetTimelineFilter`

2. **Filter Component Pattern:**
   - `BudgetTimelineFilter` demonstrates the exact pattern needed
   - Collapsible sections with badge-based selection
   - "Select All/Deselect All" functionality
   - Filter state management with `useState`

3. **UI Components:**
   - `Collapsible.Root`, `Collapsible.Trigger`, `Collapsible.Content` - Already used
   - `Badge` components for type selection (as seen in `BudgetTimelineFilter`)
   - `Checkbox` for WBE filtering (keep existing pattern)

4. **State Management:**
   - `useMemo` for normalized filter arrays (already used)
   - `useQuery` for data fetching (already used)
   - No need for context or global state

5. **Test Utilities:**
   - Mock patterns in `ProjectPerformanceDashboard.test.tsx`
   - Service mocking with `vi.mock("@/client")`
   - `renderWithProviders` utility available

## 4. ALTERNATIVE APPROACHES

### Approach 1: Replace Cost Element Selector with Type Selector (Recommended)
**Description:** Remove cost element selector entirely, replace with cost element type selector matching `BudgetTimelineFilter` pattern.

**Pros:**
- Aligns with existing `BudgetTimelineFilter` pattern
- Backend API already supports type filtering
- Simpler UI (types are fewer than individual elements)
- Better for high-level analysis
- Consistent with user request for "type performance across WBEs"

**Cons:**
- Loses ability to filter by specific individual cost elements
- May need to add cost element selector back if users need granular control

**Complexity:** Low - Well-established pattern exists
**Risk:** Low - Pattern already proven in `BudgetTimelineFilter`
**Alignment:** High - Matches existing architecture exactly

### Approach 2: Dual Selector (Type + Element)
**Description:** Keep both selectors, with type selector filtering available elements, and element selector for fine-grained control.

**Pros:**
- Maximum flexibility
- Backward compatible with existing usage
- Allows both high-level and detailed analysis

**Cons:**
- More complex UI
- Cascading filter logic required
- More state to manage
- Conflicts with user request (they asked to replace, not add)

**Complexity:** Medium - Requires cascading filter logic
**Risk:** Medium - More complexity means more edge cases
**Alignment:** Medium - Adds complexity beyond user request

### Approach 3: Type-Only with Expandable Details
**Description:** Primary filter by type, with ability to see which specific elements match within collapsed section.

**Pros:**
- Clean primary interface
- Allows verification of which elements are included
- Good UX for understanding filter impact

**Cons:**
- Requires fetching cost elements to display (currently removed)
- More complex component
- Additional API calls needed

**Complexity:** Medium-High - Requires additional data fetching
**Risk:** Medium - Additional complexity
**Alignment:** Medium - More than requested

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### Principles Followed

✅ **DRY (Don't Repeat Yourself):** Reusing `BudgetTimelineFilter` pattern
✅ **Separation of Concerns:** Filter logic separated from data display
✅ **Consistency:** Matches existing filter patterns in codebase
✅ **API-First:** Leveraging existing backend type filtering support

### Principles Violated

❌ None identified

### Maintenance Burden

**Low Impact:**
- Change is localized to one component
- No database schema changes
- No API contract changes (using existing parameter)
- Follows established patterns

**Potential Future Issues:**
- If users need individual element filtering, would need to add it back
- Type selector shows all global types, not just types present in project

### Testing Challenges

**Unit Tests:**
- Mock `CostElementTypesService.readCostElementTypes()`
- Verify filter state updates correctly
- Test type badge selection/deselection
- Test "Select All/Deselect All" functionality
- Verify API calls include `costElementTypeIds` parameter

**Integration Tests:**
- Verify filtering works end-to-end with backend
- Test drilldown items are filtered correctly by type
- Test timeline displays correct elements for selected types

**Edge Cases:**
- No types available (empty state)
- Type selected but no matching cost elements in project
- Type selection with WBE filter (combined filtering)
- Clearing filters resets type selection

### Risks and Unknowns

**Low Risk:**
- ✅ Backend API already supports type filtering
- ✅ Pattern exists and is tested in `BudgetTimelineFilter`
- ✅ No breaking changes to API contracts

**Minor Risks:**
- ⚠️ Users may want individual element filtering (addressed by Approach 2 if needed)
- ⚠️ Types are global - some may not exist in current project (UI should handle gracefully)
- ⚠️ Need to verify drilldown filtering logic works correctly with types

**Unknowns:**
- ❓ Do users need both type AND element filtering? (User request suggests no)
- ❓ Should types be filtered to only show types present in project? (Current pattern shows all active types)
- ❓ Performance impact of type-based filtering vs element-based (likely better for types)

## SUMMARY

**Feature:** Replace individual cost element selector with cost element type selector in Project Performance Dashboard to enable type-level performance analysis across WBEs.

**Recommended Approach:** Approach 1 - Direct replacement following `BudgetTimelineFilter` pattern. This is the simplest, most aligned with existing architecture, and matches user requirements.

**Key Touchpoints:**
- Replace `selectedCostElementIds` with `selectedCostElementTypeIds` throughout `ProjectPerformanceDashboard.tsx`
- Add `CostElementTypesService.readCostElementTypes()` query
- Update `FiltersCard` UI to use badge-based type selector (matching `BudgetTimelineFilter`)
- Update API calls to use `costElementTypeIds` parameter
- Update drilldown filtering logic to filter by cost element type

**Risk Level:** Low - Well-established pattern, backend support exists, localized change

**Estimated Complexity:** Low-Medium - Straightforward refactoring following existing patterns
