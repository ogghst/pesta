# Implementation Plan: Comprehensive Baseline UI Enhancement

**Plan ID:** 845716
**Based on Specification:** `docs/plans/845716-baseline-ui-enhancement-specification.md`
**Date:** 2025-11-29

## EXECUTION CONTEXT

- **TDD Discipline**: All steps follow red-green-refactor cycle
- **Human Supervision**: Pause at checkpoints for review
- **Stop/Go Criteria**: Each step has explicit acceptance criteria
- **Maximum Iterations**: 3 attempts per step before seeking help

## IMPLEMENTATION STEPS

### Phase 1: Core Baseline Metrics Display

#### Step 1.1: Regenerate OpenAPI Client [INTEGRATION]

**Description**: Regenerate the OpenAPI client to include new baseline snapshot endpoints.

**Test-First Requirement**:
- Verify new methods exist in generated client
- Test: `import { BaselineLogsService } from "@/client"; console.log(BaselineLogsService.getBaselineProjectSnapshot)`

**Implementation**:
1. Run OpenAPI client generation command
2. Verify new methods are generated
3. Check TypeScript types are correct

**Acceptance Criteria**:
- ✅ Client includes `getBaselineProjectSnapshot()` method
- ✅ Client includes `getBaselineWbeSnapshots()` method
- ✅ Client includes `getBaselineWbeSnapshotDetail()` method
- ✅ Types `BaselineWBEPublic` and `BaselineProjectPublic` exist
- ✅ No TypeScript errors
- ✅ Test: Can import and use new methods

**Expected Files**:
- `frontend/src/client/sdk.gen.ts` (AUTO-GENERATED)
- `frontend/src/client/types.gen.ts` (AUTO-GENERATED)

**Dependencies**: None (backend API must be deployed)

---

#### Step 1.2: Extract Status Indicator Utilities [UNIT]

**Description**: Extract status indicator functions to shared utility file.

**Test-First Requirement**:
- Create test: `test_status_indicators_utilities()`
- Test must fail (utilities don't exist)

**Implementation**:
1. Create `frontend/src/utils/statusIndicators.ts`
2. Extract `getCpiStatus()`, `getSpiStatus()`, `getTcpiStatus()`, `getVarianceStatus()` from EarnedValueSummary
3. Update EarnedValueSummary to use shared utilities
4. Update ProjectPerformanceDashboard to use shared utilities
5. Export all functions

**Acceptance Criteria**:
- ✅ Utility file created with all functions
- ✅ Functions work identically to original
- ✅ Existing components updated and still work
- ✅ No functionality changes
- ✅ Test passes: utilities work correctly

**Expected Files**:
- `frontend/src/utils/statusIndicators.ts` (NEW)
- `frontend/src/components/Projects/EarnedValueSummary.tsx` (MODIFY)
- `frontend/src/components/Reports/ProjectPerformanceDashboard.tsx` (MODIFY)

**Dependencies**: None

---

#### Step 1.3: Create BaselineProjectSnapshot Component [UNIT]

**Description**: Create component to display project-level baseline snapshot metrics.

**Test-First Requirement**:
- Create test: `test_baseline_project_snapshot_renders()` in `frontend/src/components/Projects/__tests__/BaselineProjectSnapshot.test.tsx`
- Test must fail (component doesn't exist)

**Implementation**:
1. Create `BaselineProjectSnapshot.tsx` component
2. Fetch project snapshot using `BaselineLogsService.getBaselineProjectSnapshot()`
3. Display metrics in card grid (similar to EarnedValueSummary)
4. Show all EVM metrics: PV, EV, AC, BAC, EAC, CPI, SPI, TCPI, CV, SV
5. Use status indicators from shared utilities
6. Handle loading and error states
7. Format currency and indices correctly

**Acceptance Criteria**:
- ✅ Component exists and renders
- ✅ Fetches data correctly
- ✅ Displays all metrics in card grid
- ✅ Shows status indicators
- ✅ Handles loading state
- ✅ Handles error state
- ✅ Handles empty/null values
- ✅ Test passes: component renders correctly

**Expected Files**:
- `frontend/src/components/Projects/BaselineProjectSnapshot.tsx` (NEW)
- `frontend/src/components/Projects/__tests__/BaselineProjectSnapshot.test.tsx` (NEW)

**Dependencies**: Steps 1.1, 1.2

---

#### Step 1.4: Create BaselineWBESnapshot Component [UNIT]

**Description**: Create component to display WBE-level baseline snapshot metrics.

**Test-First Requirement**:
- Create test: `test_baseline_wbe_snapshot_renders()` in `frontend/src/components/Projects/__tests__/BaselineWBESnapshot.test.tsx`
- Test must fail (component doesn't exist)

**Implementation**:
1. Create `BaselineWBESnapshot.tsx` component
2. Fetch WBE snapshot using `BaselineLogsService.getBaselineWbeSnapshotDetail()`
3. Display metrics in card grid (similar to BaselineProjectSnapshot)
4. Show all EVM metrics with status indicators
5. Handle loading and error states

**Acceptance Criteria**:
- ✅ Component exists and renders
- ✅ Fetches data correctly
- ✅ Displays all metrics in card grid
- ✅ Shows status indicators
- ✅ Handles loading/error states
- ✅ Test passes: component renders correctly

**Expected Files**:
- `frontend/src/components/Projects/BaselineWBESnapshot.tsx` (NEW)
- `frontend/src/components/Projects/__tests__/BaselineWBESnapshot.test.tsx` (NEW)

**Dependencies**: Steps 1.1, 1.2

---

#### Step 1.5: Enhance BaselineSummary Component [INTEGRATION]

**Description**: Add EVM indices and project snapshot data to BaselineSummary.

**Test-First Requirement**:
- Modify test: `test_baseline_summary_shows_evm_indices()`
- Test must fail (indices not displayed)

**Implementation**:
1. Fetch project snapshot data
2. Add cards for CPI, SPI, TCPI, CV, SV
3. Use status indicators from shared utilities
4. Maintain existing cards
5. Update grid layout if needed

**Acceptance Criteria**:
- ✅ Component fetches project snapshot
- ✅ Displays all EVM indices
- ✅ Shows status indicators
- ✅ Maintains existing functionality
- ✅ Test passes: all metrics displayed

**Expected Files**:
- `frontend/src/components/Projects/BaselineSummary.tsx` (MODIFY)
- `frontend/src/components/Projects/__tests__/BaselineSummary.test.tsx` (MODIFY)

**Dependencies**: Steps 1.1, 1.2, 1.3

---

#### Step 1.6: Add Project Metrics Tab to Baseline Detail [INTEGRATION]

**Description**: Add new "Project Metrics" tab to baseline detail page.

**Test-First Requirement**:
- Create test: `test_baseline_detail_has_project_metrics_tab()`
- Test must fail (tab doesn't exist)

**Implementation**:
1. Add "Project Metrics" tab to Tabs.List
2. Add Tabs.Content for project metrics
3. Use BaselineProjectSnapshot component
4. Update tab schema to include new tab
5. Update navigation logic

**Acceptance Criteria**:
- ✅ New tab appears in tab list
- ✅ Tab content shows BaselineProjectSnapshot
- ✅ Tab navigation works
- ✅ URL search params updated correctly
- ✅ Test passes: tab works correctly

**Expected Files**:
- `frontend/src/routes/_layout/projects.$id.baselines.$baselineId.tsx` (MODIFY)

**Dependencies**: Steps 1.3, 1.5

**Checkpoint**: After this step, pause and verify project-level metrics display correctly.

---

### Phase 2: WBE-Level Display and Navigation

#### Step 2.1: Create BaselineWBESnapshotsTable Component [UNIT]

**Description**: Create table component listing all WBE snapshots for a baseline.

**Test-First Requirement**:
- Create test: `test_baseline_wbe_snapshots_table_renders()`
- Test must fail (component doesn't exist)

**Implementation**:
1. Create `BaselineWBESnapshotsTable.tsx` component
2. Fetch WBE snapshots list using `BaselineLogsService.getBaselineWbeSnapshots()`
3. Define table columns (WBE name, BAC, EV, AC, CPI, SPI, etc.)
4. Use DataTable component
5. Add link column to WBE baseline detail
6. Format currency and indices
7. Add status indicators for performance indices

**Acceptance Criteria**:
- ✅ Component exists and renders
- ✅ Fetches and displays WBE snapshots
- ✅ Table shows all required columns
- ✅ Status indicators work
- ✅ Links to WBE baseline detail work
- ✅ Sorting works
- ✅ Test passes: table displays correctly

**Expected Files**:
- `frontend/src/components/Projects/BaselineWBESnapshotsTable.tsx` (NEW)
- `frontend/src/components/Projects/__tests__/BaselineWBESnapshotsTable.test.tsx` (NEW)

**Dependencies**: Steps 1.1, 1.2

---

#### Step 2.2: Add WBE Metrics Tab to Baseline Detail [INTEGRATION]

**Description**: Add new "WBE Metrics" tab showing WBE snapshots table.

**Test-First Requirement**:
- Create test: `test_baseline_detail_has_wbe_metrics_tab()`
- Test must fail (tab doesn't exist)

**Implementation**:
1. Add "WBE Metrics" tab to Tabs.List
2. Add Tabs.Content with BaselineWBESnapshotsTable
3. Update tab schema
4. Update navigation logic

**Acceptance Criteria**:
- ✅ New tab appears
- ✅ Tab shows WBE snapshots table
- ✅ Tab navigation works
- ✅ Test passes: tab works correctly

**Expected Files**:
- `frontend/src/routes/_layout/projects.$id.baselines.$baselineId.tsx` (MODIFY)

**Dependencies**: Step 2.1

---

#### Step 2.3: Enhance BaselineCostElementsByWBETable [INTEGRATION]

**Description**: Add WBE snapshot metrics to accordion headers and navigation links.

**Test-First Requirement**:
- Modify test: `test_baseline_cost_elements_by_wbe_shows_metrics()`
- Test must fail (metrics not shown)

**Implementation**:
1. Fetch WBE snapshot for each WBE in accordion
2. Display key metrics in accordion header
3. Add status indicators
4. Add link to WBE baseline detail page
5. Maintain existing cost elements display

**Acceptance Criteria**:
- ✅ Accordion headers show WBE metrics
- ✅ Status indicators displayed
- ✅ Links to WBE baseline detail work
- ✅ Existing functionality maintained
- ✅ Test passes: enhancements work

**Expected Files**:
- `frontend/src/components/Projects/BaselineCostElementsByWBETable.tsx` (MODIFY)
- `frontend/src/components/Projects/__tests__/BaselineCostElementsByWBETable.test.tsx` (MODIFY)

**Dependencies**: Steps 1.1, 1.2, 1.4

---

#### Step 2.4: Create WBE Baseline Detail Route [INTEGRATION]

**Description**: Create nested route for WBE baseline detail page.

**Test-First Requirement**:
- Create test: `test_wbe_baseline_detail_route_works()`
- Test must fail (route doesn't exist)

**Implementation**:
1. Create route file: `projects.$id.baselines.$baselineId.wbes.$wbeId.tsx`
2. Define route structure and search schema
3. Fetch baseline, project, and WBE data
4. Fetch WBE snapshot data
5. Create tabs: info, metrics, cost-elements, ai-assessment
6. Add breadcrumb navigation
7. Use BaselineWBESnapshot component for metrics tab
8. List cost elements for WBE in baseline

**Acceptance Criteria**:
- ✅ Route exists and is accessible
- ✅ Fetches all required data
- ✅ Shows WBE snapshot metrics
- ✅ Lists cost elements correctly
- ✅ Breadcrumb navigation works
- ✅ Tab navigation works
- ✅ Test passes: route works correctly

**Expected Files**:
- `frontend/src/routes/_layout/projects.$id.baselines.$baselineId.wbes.$wbeId.tsx` (NEW)

**Dependencies**: Steps 1.1, 1.4, 2.1

**Checkpoint**: After this step, pause and verify WBE baseline detail page works correctly.

---

#### Step 2.5: Add Navigation Links [INTEGRATION]

**Description**: Add navigation links throughout baseline views.

**Test-First Requirement**:
- Create test: `test_baseline_navigation_links_work()`
- Test must fail (links don't work)

**Implementation**:
1. Add links in BaselineWBESnapshotsTable to WBE baseline detail
2. Add links in BaselineCostElementsByWBETable to WBE baseline detail
3. Add breadcrumb links in WBE baseline detail
4. Ensure links preserve baseline context
5. Test all navigation paths

**Acceptance Criteria**:
- ✅ All navigation links work
- ✅ Links preserve context
- ✅ Breadcrumbs work correctly
- ✅ Navigation is intuitive
- ✅ Test passes: all links work

**Expected Files**:
- Multiple files (MODIFY)

**Dependencies**: Step 2.4

---

### Phase 3: Testing and Polish

#### Step 3.1: Component Tests [UNIT]

**Description**: Write comprehensive tests for all new components.

**Test-First Requirement**:
- Tests should already exist from previous steps
- Verify all tests pass

**Implementation**:
1. Review and enhance existing tests
2. Add edge case tests
3. Add error handling tests
4. Add loading state tests
5. Ensure good test coverage

**Acceptance Criteria**:
- ✅ All components have tests
- ✅ Tests cover success, loading, error states
- ✅ Tests cover edge cases
- ✅ Test coverage > 80%
- ✅ All tests pass

**Expected Files**:
- Test files in `__tests__` folders (NEW/MODIFY)

**Dependencies**: All previous steps

---

#### Step 3.2: Integration Tests [INTEGRATION]

**Description**: Test navigation and data flow between components.

**Test-First Requirement**:
- Create integration tests
- Tests must verify full user flows

**Implementation**:
1. Test baseline detail page navigation
2. Test WBE baseline detail page
3. Test data fetching and caching
4. Test error handling
5. Test responsive behavior

**Acceptance Criteria**:
- ✅ Integration tests cover main flows
- ✅ Navigation tests pass
- ✅ Data flow tests pass
- ✅ Error handling tests pass
- ✅ All tests pass

**Expected Files**:
- Integration test files (NEW)

**Dependencies**: All previous steps

---

#### Step 3.3: E2E Tests [E2E]

**Description**: End-to-end tests for complete baseline UI workflow.

**Test-First Requirement**:
- Create Playwright E2E tests
- Tests must verify complete user journey

**Implementation**:
1. Test baseline creation → viewing → navigation
2. Test drill-down from project → WBE → cost element
3. Test tab navigation
4. Test responsive behavior
5. Test error scenarios

**Acceptance Criteria**:
- ✅ E2E tests cover main workflows
- ✅ All E2E tests pass
- ✅ Tests are stable and reliable

**Expected Files**:
- Playwright test files (NEW)

**Dependencies**: All previous steps

**Final Checkpoint**: After this step, verify complete implementation works end-to-end.

---

## TDD DISCIPLINE RULES

1. **Red Phase**: Write failing test first
2. **Green Phase**: Write minimal code to make test pass
3. **Refactor Phase**: Improve code while keeping tests green
4. **Maximum Iterations**: 3 attempts per step before asking for help
5. **Test Coverage**: All new code must have tests
6. **No Production Code Without Tests**: Every production change must have corresponding test

## PROCESS CHECKPOINTS

**Checkpoint 1**: After Step 1.6 (Project Metrics Tab)
- Question: "Does project-level baseline metrics display correctly?"
- Question: "Are all EVM indices showing with proper status indicators?"
- Action: Test project metrics display, verify styling consistency

**Checkpoint 2**: After Step 2.4 (WBE Baseline Detail Route)
- Question: "Does WBE baseline detail page work correctly?"
- Question: "Is navigation intuitive and working?"
- Action: Test WBE baseline detail, verify all features work

**Final Checkpoint**: After Step 3.3 (E2E Tests)
- Question: "Is the complete implementation working?"
- Question: "Are there any remaining issues?"
- Action: Review complete implementation, verify all requirements met

## SCOPE BOUNDARIES

**In Scope (Phase 1)**:
- Project-level baseline metrics display
- WBE-level baseline metrics display
- WBE baseline detail page
- Navigation between levels
- Status indicators and formatting
- Loading and error states

**Out of Scope (Phase 2 - Future)**:
- Baseline comparison (compare two baselines)
- Baseline trend charts
- Export functionality
- Enhanced visualizations
- Baseline to operational view switching

**If Useful Improvements Found**:
- Ask user for confirmation before implementing
- Document in separate enhancement request

## ROLLBACK STRATEGY

**Safe Rollback Points**:

1. **After Step 1.2**: Remove utility file, revert component changes
   - No breaking changes
   - Existing functionality unchanged

2. **After Step 1.6**: Remove new tab, keep existing tabs
   - No breaking changes
   - Existing baseline views unchanged

3. **After Step 2.4**: Remove WBE baseline route
   - No breaking changes
   - Existing routes unchanged

**Alternative Approach if Current Fails**:
- If tab-based approach fails, consider:
  - Modal-based approach (simpler but less intuitive)
  - Single comprehensive dashboard (different UX)
- Must get user approval before switching approaches

## IMPLEMENTATION NOTES

### Code Quality Standards
- Follow existing code style (Biome)
- Use TypeScript for type safety
- Follow component patterns
- Use Chakra UI components consistently
- No linting errors

### Testing Standards
- Unit tests for components
- Integration tests for navigation
- E2E tests for workflows
- Test loading, error, and success states
- Test responsive behavior

### Documentation
- Component docstrings
- Type definitions
- Update README if needed

## ESTIMATED TIMELINE

- **Phase 1**: ~3.5 hours (Core Baseline Metrics Display)
- **Phase 2**: ~4.5 hours (WBE-Level Display and Navigation)
- **Phase 3**: ~2.5 hours (Testing and Polish)

**Total Estimated Time**: ~10.5 hours

*Note: Times are estimates and may vary based on complexity and debugging needs.*

## PHASE 2 TASKS (Future Enhancements)

### Task P2.1: Baseline Comparison Feature
- **Description**: Compare two baselines side-by-side
- **Complexity**: High
- **Estimated Time**: 8-10 hours
- **Dependencies**: Phase 1 complete

### Task P2.2: Baseline Trend Charts
- **Description**: Show baseline metrics trends over time
- **Complexity**: Medium
- **Estimated Time**: 6-8 hours
- **Dependencies**: Phase 1 complete

### Task P2.3: Export Functionality
- **Description**: Export baseline reports to PDF/Excel
- **Complexity**: Medium-High
- **Estimated Time**: 8-10 hours
- **Dependencies**: Phase 1 complete

### Task P2.4: Baseline to Operational Navigation
- **Description**: Easy navigation from baseline to operational views
- **Complexity**: Low-Medium
- **Estimated Time**: 4-6 hours
- **Dependencies**: Phase 1 complete

### Task P2.5: Enhanced Visualizations
- **Description**: Add more charts for baseline data
- **Complexity**: Medium
- **Estimated Time**: 6-8 hours
- **Dependencies**: Phase 1 complete
