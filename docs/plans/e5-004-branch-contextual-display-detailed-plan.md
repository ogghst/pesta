# E5-004 Branch Contextual Display - Detailed Implementation Plan

**Task:** E5-004 (Branch Contextual Display - Show Full Project Context in Branch Views)
**Status:** Planning Complete - Ready for Implementation
**Date:** 2025-11-27
**Last Updated:** 2025-11-27 06:33 CET (Europe/Rome)
**Analysis Document:** `docs/analysis/e5-004-branch-contextual-display-analysis.md`
**Approach:** Merged View with Visual Indicators (Approach A)

---

## EXECUTION CONTEXT

- This plan will be implemented using TDD discipline with human supervision
- Implementation will occur in steps within this conversation thread
- Each step must have clear stop/go criteria
- Maximum 3 iteration attempts per step before stopping to ask for help
- Red-green-refactor cycle must be followed for each step

---

## TDD DISCIPLINE RULES

1. **Failing test MUST exist before any production code changes**
2. **Maximum 3 iteration attempts per step** before stopping to ask for help
3. **Red-green-refactor cycle** must be followed for each step:
   - Red: Write failing test
   - Green: Write minimal code to pass test
   - Refactor: Improve code while keeping tests passing
4. **Tests must verify behavior, not just compilation**
5. **All tests must pass before moving to next step**

---

## CONFIRMED REQUIREMENTS

Based on user clarifications:

- **Change Status Calculation:** Use branch comparison API (`compare_branches()` endpoint)
- **Deleted Entities:** Show in merged view with strikethrough
- **Version Selection:** Latest active version per branch
- **View Mode Default:** Merged (not branch-only)
- **Performance:** No performance threshold (optimize as needed)
- **Cache Invalidation:** Merged view invalidated on branch change
- **Mobile View:** Same indicators as desktop
- **Delete Behavior:** Soft delete in branch (creates delete marker)
- **Edit Behavior:** If entity only exists in main, create new version in branch

---

## SCOPE BOUNDARIES

**IN SCOPE:**
- Merged view for WBEs and Cost Elements
- Visual change indicators (created, updated, deleted, unchanged)
- View mode toggle (branch-only vs merged)
- Integration with branch comparison API for change status
- Soft delete functionality for main-only entities
- Edit functionality that creates branch versions for main-only entities
- Query invalidation on branch change

**OUT OF SCOPE:**
- Performance optimizations (unless critical)
- Caching layer (unless performance issues arise)
- Separate mobile UI (same indicators)
- Other entity types (only WBE and CostElement)
- Branch comparison UI enhancements (reuse existing)

---

## ROLLBACK STRATEGY

**Safe Rollback Points:**
1. **After Step 2 (Backend Service):** Can revert service file, no API changes yet
2. **After Step 4 (Backend API):** Can revert API endpoints, frontend not updated yet
3. **After Step 6 (Frontend Context):** Can revert context changes, components not updated yet
4. **After Step 8 (Visual Indicators):** Can revert indicator components, keep merged view

**Alternative Approach:**
- If merged view proves too complex, can fall back to Approach C (Overlay/Modal Comparison)
- Keep branch-only as default, add "Compare with Main" button that opens comparison overlay

---

## IMPLEMENTATION STEPS

### Step 1: Create Backend Merged View Service - WBE Support

**Objective:** Create service function to get merged WBE view (main + branch entities) with change status.

**Test-First Requirement:**
- Create failing test: `backend/tests/services/test_merged_view_service.py`
- Test: `get_merged_wbes()` returns all main branch WBEs + branch WBEs
- Test: `get_merged_wbes()` marks entities with correct change status (created, updated, deleted, unchanged)
- Test: `get_merged_wbes()` uses branch comparison API to determine change status
- Test: `get_merged_wbes()` returns latest active version per branch
- Test: `get_merged_wbes()` includes deleted entities with deleted status
- Test: `get_merged_wbes()` handles empty branches correctly

**Acceptance Criteria:**
- ✅ `get_merged_wbes()` function exists in `backend/app/services/merged_view_service.py`
- ✅ Function fetches all active WBEs from main branch
- ✅ Function fetches all active WBEs from specified branch
- ✅ Function calls branch comparison API to get change status
- ✅ Function merges results with branch entities taking precedence
- ✅ Function marks entities with change status: "created", "updated", "deleted", "unchanged"
- ✅ Function includes deleted entities (status='deleted' in branch)
- ✅ Function returns latest active version per branch
- ✅ All tests pass

**Files to Create:**
- `backend/app/services/merged_view_service.py`
- `backend/tests/services/test_merged_view_service.py`

**Dependencies:**
- None (first step, uses existing branch comparison API)

**Estimated Time:** 2-3 hours

---

### Step 2: Create Backend Merged View Service - Cost Element Support

**Objective:** Extend merged view service to support Cost Elements.

**Test-First Requirement:**
- Update test: `backend/tests/services/test_merged_view_service.py`
- Test: `get_merged_cost_elements()` returns all main branch cost elements + branch cost elements
- Test: `get_merged_cost_elements()` marks entities with correct change status
- Test: `get_merged_cost_elements()` uses branch comparison API
- Test: `get_merged_cost_elements()` handles cost elements within WBEs correctly
- Test: `get_merged_cost_elements()` includes deleted entities

**Acceptance Criteria:**
- ✅ `get_merged_cost_elements()` function exists in merged_view_service.py
- ✅ Function follows same pattern as `get_merged_wbes()`
- ✅ Function handles WBE relationships correctly
- ✅ Function uses branch comparison API for change status
- ✅ All tests pass

**Files to Modify:**
- `backend/app/services/merged_view_service.py`
- `backend/tests/services/test_merged_view_service.py`

**Dependencies:**
- Step 1 (WBE merged view service must exist)

**Estimated Time:** 2-3 hours

---

### Step 3: Add View Mode Parameter to WBE API Endpoint

**Objective:** Add `view_mode` parameter to WBE GET endpoints to support merged view.

**Test-First Requirement:**
- Update test: `backend/tests/api/routes/test_wbes.py`
- Test: `read_wbes()` with `view_mode='branch-only'` returns only branch entities (existing behavior)
- Test: `read_wbes()` with `view_mode='merged'` returns merged view with change status
- Test: `read_wbes()` defaults to `view_mode='merged'` (new default)
- Test: `read_wbes()` with `view_mode='merged'` includes change_status field in response
- Test: `read_wbe()` (single entity) supports view_mode parameter

**Acceptance Criteria:**
- ✅ `view_mode` parameter added to `read_wbes()` endpoint
- ✅ `view_mode` parameter added to `read_wbe()` endpoint
- ✅ Default value is `'merged'` (not `'branch-only'`)
- ✅ `view_mode='branch-only'` maintains existing behavior
- ✅ `view_mode='merged'` calls merged view service and includes change_status
- ✅ Response includes `change_status` field when view_mode='merged'
- ✅ All existing WBE API tests still pass
- ✅ New merged view tests pass

**Files to Modify:**
- `backend/app/api/routes/wbes.py`
- `backend/tests/api/routes/test_wbes.py`

**Dependencies:**
- Step 1 (Merged view service must exist)

**Estimated Time:** 2-3 hours

---

### Step 4: Add View Mode Parameter to Cost Element API Endpoint

**Objective:** Add `view_mode` parameter to Cost Element GET endpoints to support merged view.

**Test-First Requirement:**
- Update test: `backend/tests/api/routes/test_cost_elements.py`
- Test: `read_cost_elements()` with `view_mode='branch-only'` returns only branch entities
- Test: `read_cost_elements()` with `view_mode='merged'` returns merged view with change status
- Test: `read_cost_elements()` defaults to `view_mode='merged'`
- Test: `read_cost_element()` (single entity) supports view_mode parameter

**Acceptance Criteria:**
- ✅ `view_mode` parameter added to `read_cost_elements()` endpoint
- ✅ `view_mode` parameter added to `read_cost_element()` endpoint
- ✅ Default value is `'merged'`
- ✅ `view_mode='merged'` calls merged view service and includes change_status
- ✅ All existing Cost Element API tests still pass
- ✅ New merged view tests pass

**Files to Modify:**
- `backend/app/api/routes/cost_elements.py`
- `backend/tests/api/routes/test_cost_elements.py`

**Dependencies:**
- Step 2 (Cost Element merged view service must exist)
- Step 3 (WBE API pattern established)

**Estimated Time:** 2-3 hours

---

### Step 5: Regenerate OpenAPI Client

**Objective:** Regenerate frontend OpenAPI client with new `view_mode` parameter and `change_status` field.

**Test-First Requirement:**
- Verify: OpenAPI client includes `view_mode` parameter in WBE/CostElement endpoints
- Verify: TypeScript types include `change_status` field in response types
- Verify: Client can be imported in frontend

**Acceptance Criteria:**
- ✅ OpenAPI client regenerated
- ✅ `view_mode` parameter included in WBE/CostElement query types
- ✅ `change_status` field included in WBE/CostElement response types
- ✅ TypeScript types generated correctly
- ✅ Client imports work in frontend

**Files to Modify:**
- `frontend/src/client/` (regenerated)

**Dependencies:**
- Step 3, 4 (API endpoints must have view_mode parameter)

**Estimated Time:** 30 minutes

---

### Step 6: Extend Branch Context with View Mode

**Objective:** Add view mode state to BranchContext to support merged/branch-only toggle.

**Test-First Requirement:**
- Update test: `frontend/src/context/BranchContext.test.tsx`
- Test: `BranchContext` includes `viewMode` state (default: 'merged')
- Test: `setViewMode()` function updates view mode
- Test: View mode persists in localStorage per project
- Test: View mode resets to 'merged' when branch changes (invalidation)

**Acceptance Criteria:**
- ✅ `BranchContext` includes `viewMode: 'branch-only' | 'merged'`
- ✅ Default value is `'merged'`
- ✅ `setViewMode()` function exists
- ✅ View mode persists in localStorage (key: `view-mode-${projectId}`)
- ✅ View mode resets to 'merged' when branch changes
- ✅ All existing BranchContext tests still pass
- ✅ New view mode tests pass

**Files to Modify:**
- `frontend/src/context/BranchContext.tsx`
- `frontend/src/context/BranchContext.test.tsx` (if exists, or create)

**Dependencies:**
- Step 5 (OpenAPI client must be regenerated)

**Estimated Time:** 1-2 hours

---

### Step 7: Create View Mode Toggle Component

**Objective:** Create UI component to toggle between branch-only and merged view modes.

**Test-First Requirement:**
- Create test: `frontend/src/components/Projects/ViewModeToggle.test.tsx`
- Test: Component renders toggle with current view mode
- Test: Component calls `setViewMode()` when toggled
- Test: Component shows "Branch Only" and "Merged View" options
- Test: Component uses Chakra UI RadioGroup or Toggle component

**Acceptance Criteria:**
- ✅ `ViewModeToggle` component exists
- ✅ Component uses Chakra UI components (RadioGroup or Toggle)
- ✅ Component integrates with `useBranch()` hook
- ✅ Component updates view mode on change
- ✅ Component shows current view mode
- ✅ All tests pass

**Files to Create:**
- `frontend/src/components/Projects/ViewModeToggle.tsx`
- `frontend/src/components/Projects/ViewModeToggle.test.tsx`

**Dependencies:**
- Step 6 (BranchContext must have viewMode)

**Estimated Time:** 1-2 hours

---

### Step 8: Create Change Status Indicator Component

**Objective:** Create reusable component to display change status indicators (created, updated, deleted, unchanged).

**Test-First Requirement:**
- Create test: `frontend/src/components/Projects/ChangeStatusIndicator.test.tsx`
- Test: Component renders green badge for "created" status
- Test: Component renders yellow badge for "updated" status
- Test: Component renders red badge for "deleted" status
- Test: Component renders nothing for "unchanged" status
- Test: Component is accessible (screen reader support)
- Test: Component works on mobile (same indicators)

**Acceptance Criteria:**
- ✅ `ChangeStatusIndicator` component exists
- ✅ Component accepts `changeStatus: 'created' | 'updated' | 'deleted' | 'unchanged'`
- ✅ Component uses Chakra UI Badge component
- ✅ Visual indicators:
  - Created: Green badge with "+" icon
  - Updated: Yellow badge with "~" icon
  - Deleted: Red badge with "×" icon
  - Unchanged: No indicator
- ✅ Component is accessible (aria-label, color contrast)
- ✅ Component is responsive (works on mobile)
- ✅ All tests pass

**Files to Create:**
- `frontend/src/components/Projects/ChangeStatusIndicator.tsx`
- `frontend/src/components/Projects/ChangeStatusIndicator.test.tsx`

**Dependencies:**
- None (standalone component)

**Estimated Time:** 1-2 hours

---

### Step 9: Update WBE DataTable with Change Indicators

**Objective:** Integrate change indicators into WBE table and update queries to use view mode.

**Test-First Requirement:**
- Update test: `frontend/src/routes/_layout/projects.$id.test.tsx` (if exists)
- Test: WBE table includes change status column when viewMode='merged'
- Test: WBE table shows change indicators for each row
- Test: WBE table queries use viewMode from context
- Test: WBE table invalidates queries when viewMode changes
- Test: Deleted WBEs show with strikethrough styling

**Acceptance Criteria:**
- ✅ WBE table queries include `view_mode` parameter from context
- ✅ WBE table includes change status column (when merged view)
- ✅ WBE table shows `ChangeStatusIndicator` for each row
- ✅ Deleted WBEs display with strikethrough (text-decoration: line-through)
- ✅ Query keys include viewMode for proper invalidation
- ✅ All existing WBE table tests still pass
- ✅ New merged view tests pass

**Files to Modify:**
- `frontend/src/routes/_layout/projects.$id.tsx` (WBEsTable component)
- `frontend/src/routes/_layout/projects.$id.test.tsx` (if exists)

**Dependencies:**
- Step 7 (ViewModeToggle must exist)
- Step 8 (ChangeStatusIndicator must exist)
- Step 6 (BranchContext must have viewMode)

**Estimated Time:** 2-3 hours

---

### Step 10: Update Cost Element DataTable with Change Indicators

**Objective:** Integrate change indicators into Cost Element table and update queries to use view mode.

**Test-First Requirement:**
- Update test: `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.test.tsx` (if exists)
- Test: Cost Element table includes change status column when viewMode='merged'
- Test: Cost Element table shows change indicators
- Test: Cost Element table queries use viewMode from context
- Test: Deleted cost elements show with strikethrough

**Acceptance Criteria:**
- ✅ Cost Element table queries include `view_mode` parameter from context
- ✅ Cost Element table includes change status column (when merged view)
- ✅ Cost Element table shows `ChangeStatusIndicator` for each row
- ✅ Deleted cost elements display with strikethrough
- ✅ Query keys include viewMode for proper invalidation
- ✅ All existing Cost Element table tests still pass
- ✅ New merged view tests pass

**Files to Modify:**
- `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.tsx` (CostElementsTable component)
- `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.test.tsx` (if exists)

**Dependencies:**
- Step 9 (WBE table pattern established)
- Step 8 (ChangeStatusIndicator must exist)

**Estimated Time:** 2-3 hours

---

### Step 11: Integrate View Mode Toggle into Branch Selector

**Objective:** Add view mode toggle to BranchSelector component or nearby location.

**Test-First Requirement:**
- Update test: `frontend/src/components/Projects/BranchSelector.test.tsx`
- Test: ViewModeToggle appears in BranchSelector or nearby
- Test: View mode toggle is visible when branch is not 'main'
- Test: View mode toggle works correctly

**Acceptance Criteria:**
- ✅ ViewModeToggle integrated into UI (BranchSelector or project header)
- ✅ Toggle is visible when viewing change order branches
- ✅ Toggle may be hidden or disabled when branch='main' (optional)
- ✅ Toggle updates view mode correctly
- ✅ All existing BranchSelector tests still pass

**Files to Modify:**
- `frontend/src/components/Projects/BranchSelector.tsx`
- OR `frontend/src/routes/_layout/projects.$id.tsx` (project header)
- `frontend/src/components/Projects/BranchSelector.test.tsx`

**Dependencies:**
- Step 7 (ViewModeToggle must exist)
- Step 9, 10 (Tables must support view mode)

**Estimated Time:** 1-2 hours

---

### Step 12: Update Delete Functionality for Main-Only Entities

**Objective:** Enable deleting entities that exist only in main branch (creates soft delete in branch).

**Test-First Requirement:**
- Update test: `backend/tests/api/routes/test_wbes.py`
- Test: DELETE endpoint for WBE in merged view creates delete marker in branch
- Test: DELETE endpoint for main-only WBE creates new version in branch with status='deleted'
- Test: DELETE endpoint for branch WBE performs normal soft delete
- Test: Same behavior for Cost Elements

**Acceptance Criteria:**
- ✅ DELETE endpoint checks if entity exists in current branch
- ✅ If entity only exists in main, create new version in branch with status='deleted'
- ✅ If entity exists in branch, perform normal soft delete (update status)
- ✅ Works for both WBEs and Cost Elements
- ✅ All existing delete tests still pass
- ✅ New merged view delete tests pass

**Files to Modify:**
- `backend/app/api/routes/wbes.py` (DELETE endpoint)
- `backend/app/api/routes/cost_elements.py` (DELETE endpoint)
- `backend/tests/api/routes/test_wbes.py`
- `backend/tests/api/routes/test_cost_elements.py`

**Dependencies:**
- Step 3, 4 (API endpoints must support view_mode)

**Estimated Time:** 2-3 hours

---

### Step 13: Update Edit Functionality for Main-Only Entities

**Objective:** Enable editing entities that exist only in main branch (creates new version in branch).

**Test-First Requirement:**
- Update test: `backend/tests/api/routes/test_wbes.py`
- Test: UPDATE endpoint for WBE in merged view checks if entity exists in branch
- Test: UPDATE endpoint for main-only WBE creates new version in branch
- Test: UPDATE endpoint for branch WBE performs normal version increment
- Test: Same behavior for Cost Elements

**Acceptance Criteria:**
- ✅ UPDATE endpoint checks if entity exists in current branch
- ✅ If entity only exists in main, create new version in branch with user's changes
- ✅ If entity exists in branch, perform normal version increment
- ✅ Works for both WBEs and Cost Elements
- ✅ All existing update tests still pass
- ✅ New merged view update tests pass

**Files to Modify:**
- `backend/app/api/routes/wbes.py` (UPDATE endpoint)
- `backend/app/api/routes/cost_elements.py` (UPDATE endpoint)
- `backend/tests/api/routes/test_wbes.py`
- `backend/tests/api/routes/test_cost_elements.py`

**Dependencies:**
- Step 12 (Delete pattern established)

**Estimated Time:** 2-3 hours

---

### Step 14: Add Query Invalidation on Branch Change

**Objective:** Ensure merged view queries are invalidated when branch changes.

**Test-First Requirement:**
- Update test: `frontend/src/context/BranchContext.test.tsx`
- Test: `setCurrentBranch()` invalidates queries with viewMode in key
- Test: Query invalidation includes WBE and Cost Element queries
- Test: View mode resets to 'merged' on branch change

**Acceptance Criteria:**
- ✅ `setCurrentBranch()` invalidates queries that include viewMode
- ✅ Query invalidation includes `["wbes", ...]` and `["cost-elements", ...]` queries
- ✅ View mode resets to 'merged' when branch changes
- ✅ All existing invalidation tests still pass

**Files to Modify:**
- `frontend/src/context/BranchContext.tsx`
- `frontend/src/context/BranchContext.test.tsx`

**Dependencies:**
- Step 6 (BranchContext must exist)
- Step 9, 10 (Queries must include viewMode in keys)

**Estimated Time:** 1 hour

---

### Step 15: Add Strikethrough Styling for Deleted Entities

**Objective:** Apply strikethrough styling to deleted entities in merged view.

**Test-First Requirement:**
- Update test: `frontend/src/components/Projects/ChangeStatusIndicator.test.tsx`
- Test: Deleted entities show strikethrough text
- Test: Strikethrough works with Chakra UI Text component
- Test: Strikethrough is visible and accessible

**Acceptance Criteria:**
- ✅ Deleted entities display with `textDecoration: 'line-through'`
- ✅ Strikethrough applied to entity name/description in table
- ✅ Strikethrough works with Chakra UI components
- ✅ Strikethrough is visible and doesn't break layout
- ✅ All tests pass

**Files to Modify:**
- `frontend/src/routes/_layout/projects.$id.tsx` (WBE table cell renderers)
- `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.tsx` (Cost Element table cell renderers)
- `frontend/src/components/Projects/ChangeStatusIndicator.test.tsx`

**Dependencies:**
- Step 9, 10 (Tables must exist)
- Step 8 (ChangeStatusIndicator must exist)

**Estimated Time:** 1 hour

---

## PROCESS CHECKPOINTS

**Checkpoint 1: After Step 2 (Backend Service Complete)**
- ✅ Does merged view service work correctly?
- ✅ Are change statuses calculated correctly using branch comparison API?
- ✅ Should we continue with API endpoint updates?

**Checkpoint 2: After Step 4 (Backend API Complete)**
- ✅ Do API endpoints support view_mode parameter correctly?
- ✅ Is default value 'merged' working?
- ✅ Should we continue with frontend implementation?

**Checkpoint 3: After Step 10 (Frontend Tables Complete)**
- ✅ Do tables show change indicators correctly?
- ✅ Is merged view displaying all entities?
- ✅ Should we continue with delete/edit functionality?

**Checkpoint 4: After Step 15 (Complete Implementation)**
- ✅ Is merged view working correctly?
- ✅ Can users delete main-only entities?
- ✅ Can users edit main-only entities?
- ✅ Are queries invalidated on branch change?
- ✅ Is the implementation ready for testing?

---

## ESTIMATED TOTAL TIME

**Backend Implementation:** 10-15 hours
- Merged view service: 4-6 hours
- API endpoint updates: 4-6 hours
- Delete/Edit functionality: 4-6 hours

**Frontend Implementation:** 10-15 hours
- Context and toggle: 2-4 hours
- Change indicators: 2-4 hours
- Table integration: 4-6 hours
- Styling and polish: 2-3 hours

**Testing:** Included in above estimates (TDD approach)

**Total:** 20-30 hours

---

## SUCCESS CRITERIA

**Backend Implementation Complete When:**
- ✅ Merged view service returns all entities with correct change status
- ✅ Change status calculated using branch comparison API
- ✅ API endpoints support view_mode parameter (default: 'merged')
- ✅ Delete functionality works for main-only entities
- ✅ Edit functionality works for main-only entities
- ✅ All tests passing

**Frontend Implementation Complete When:**
- ✅ View mode toggle visible and functional
- ✅ Change indicators display correctly (created, updated, deleted, unchanged)
- ✅ WBE and Cost Element tables show merged view
- ✅ Deleted entities show with strikethrough
- ✅ Queries invalidate on branch change
- ✅ View mode defaults to 'merged'
- ✅ All tests passing

**User Experience Complete When:**
- ✅ Users can see full project context in branch views
- ✅ Users can understand impact of changes (visual indicators)
- ✅ Users can delete main-only entities
- ✅ Users can edit main-only entities
- ✅ View mode toggle is intuitive and accessible
- ✅ Mobile experience works (same indicators)

---

## NOTES

- **Default View Mode:** Changed from 'branch-only' to 'merged' per user requirement
- **Change Status:** Uses existing branch comparison API (no new calculation logic)
- **Performance:** No specific thresholds, optimize as needed
- **Mobile:** Same indicators as desktop (no separate mobile UI)
- **Backward Compatibility:** 'branch-only' mode still available via toggle

---

**Plan Status:** Detailed Plan Complete - Ready for Implementation
**Next Action:** Begin Step 1 - Create Backend Merged View Service (WBE Support)
