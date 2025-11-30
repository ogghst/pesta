# Detailed Specification: Comprehensive Baseline UI Enhancement

**Specification ID:** 845716
**Based on Analysis:** `docs/analysis/845716-baseline-ui-enhancement-analysis.md`
**Date:** 2025-11-29

## 1. FEATURE SPECIFICATION

### 1.1 User-Facing Description

**What users will be able to do:**

1. **View Project-Level Baseline Metrics**:
   - See comprehensive EVM metrics at project level (PV, EV, AC, BAC, EAC, CPI, SPI, TCPI, CV, SV)
   - View metrics in card grid layout with status indicators
   - Understand project performance at baseline creation

2. **View WBE-Level Baseline Metrics**:
   - See EVM metrics for each WBE in the baseline
   - Navigate to WBE baseline detail page
   - Compare WBE performance within baseline
   - Drill down from project to WBE level

3. **Navigate Hierarchically**:
   - Navigate from baseline project view → WBE baseline view → cost element details
   - Use breadcrumb navigation to understand context
   - Switch between baseline and operational views

4. **Compare Baseline Performance**:
   - See performance indices (CPI, SPI, TCPI) at all levels
   - Understand cost and schedule variances
   - Identify underperforming WBEs or cost elements

### 1.2 Success Criteria

**Functional Success:**
- ✅ Baseline detail page shows project-level metrics with all EVM indices
- ✅ Baseline detail page shows WBE-level metrics in table/list
- ✅ Users can navigate to WBE baseline detail page
- ✅ WBE baseline detail page shows WBE metrics and cost elements
- ✅ All metrics display with proper formatting and status indicators
- ✅ Navigation works correctly (breadcrumbs, links, tabs)
- ✅ Empty states handled gracefully
- ✅ Loading states shown during data fetching

**Visual Success:**
- ✅ Consistent styling with existing baseline components
- ✅ Status indicators (colors, icons) match operational views
- ✅ Responsive layout works on mobile and desktop
- ✅ Theme support (light/dark mode)

**Performance Success:**
- ✅ Page loads within 2 seconds
- ✅ Smooth navigation between views
- ✅ No unnecessary re-renders

**Data Integrity Success:**
- ✅ Metrics match backend snapshot data
- ✅ Time machine control date respected
- ✅ Data consistency between levels (project = sum of WBEs)

### 1.3 Edge Cases

1. **Empty Baseline**: Baseline with no WBEs or cost elements
   - Should show zero metrics
   - Should show appropriate empty state message
   - Should not crash or error

2. **Missing Snapshot Data**: Baseline created before snapshot feature
   - Should handle gracefully (show message or fallback)
   - Should not break existing functionality

3. **Large Projects**: Projects with many WBEs (20+)
   - Should handle pagination or virtualization
   - Should maintain performance
   - Should allow filtering/searching

4. **Null/Undefined Metrics**: Metrics that are null or undefined
   - Should display "N/A" appropriately
   - Should not break calculations
   - Should handle in status indicators

5. **Navigation Edge Cases**:
   - Invalid baseline ID → 404 page
   - Invalid WBE ID → 404 page
   - Navigation from baseline to operational view
   - Browser back/forward navigation

### 1.4 Error Conditions

1. **API Errors**: Failed to fetch baseline snapshot data
   - **Response**: Show error message
   - **UI**: Error state with retry option
   - **Logging**: Log error for debugging

2. **Network Errors**: Connection timeout or network failure
   - **Response**: Show network error message
   - **UI**: Retry button
   - **Behavior**: Preserve navigation state

3. **Invalid Data**: Malformed response from API
   - **Response**: Show data error message
   - **UI**: Fallback to safe defaults
   - **Logging**: Log error with response data

4. **Missing Dependencies**: Required data not available
   - **Response**: Show loading or empty state
   - **UI**: Disable dependent features
   - **Behavior**: Graceful degradation

## 2. TECHNICAL SPECIFICATION

### 2.1 Interfaces to Create or Modify

#### 2.1.1 New Components

**`BaselineProjectSnapshot.tsx`** (`frontend/src/components/Projects/BaselineProjectSnapshot.tsx`)
- **Purpose**: Display project-level baseline snapshot metrics
- **Props**: `{ projectId: string, baselineId: string }`
- **Features**:
  - Fetches project snapshot from API
  - Displays all EVM metrics in card grid
  - Shows status indicators for performance indices
  - Loading and error states
- **Pattern**: Similar to EarnedValueSummary but uses baseline snapshot data

**`BaselineWBESnapshot.tsx`** (`frontend/src/components/Projects/BaselineWBESnapshot.tsx`)
- **Purpose**: Display WBE-level baseline snapshot metrics
- **Props**: `{ projectId: string, baselineId: string, wbeId: string }`
- **Features**:
  - Fetches WBE snapshot from API
  - Displays all EVM metrics in card grid
  - Shows status indicators
  - Loading and error states
- **Pattern**: Similar to EarnedValueSummary but uses baseline snapshot data

**`BaselineMetricsSummary.tsx`** (`frontend/src/components/Projects/BaselineMetricsSummary.tsx`)
- **Purpose**: Reusable component for baseline metrics at any level
- **Props**: `{ level: "project" | "wbe" | "cost-element", projectId: string, baselineId: string, wbeId?: string, costElementId?: string }`
- **Features**:
  - Fetches appropriate baseline snapshot
  - Displays metrics in card grid
  - Composable with other summary components
- **Pattern**: Similar to MetricsSummary but for baseline data

**`BaselineWBESnapshotsTable.tsx`** (`frontend/src/components/Projects/BaselineWBESnapshotsTable.tsx`)
- **Purpose**: Table/list of WBE snapshots for a baseline
- **Props**: `{ projectId: string, baselineId: string }`
- **Features**:
  - Lists all WBE snapshots
  - Shows key metrics in table
  - Links to WBE baseline detail
  - Sorting and filtering
- **Pattern**: Similar to BaselineCostElementsTable

#### 2.1.2 Modified Components

**`BaselineSummary.tsx`** (MODIFY)
- **Enhancement**: Add EVM indices (CPI, SPI, TCPI, CV, SV)
- **Enhancement**: Fetch and display project snapshot data
- **Enhancement**: Add status indicators for performance indices

**`BaselineCostElementsByWBETable.tsx`** (MODIFY)
- **Enhancement**: Add WBE snapshot metrics display in accordion header
- **Enhancement**: Add link to WBE baseline detail page
- **Enhancement**: Show EVM indices for each WBE

**`projects.$id.baselines.$baselineId.tsx`** (MODIFY)
- **Enhancement**: Add new tabs: "project-metrics", "wbe-metrics"
- **Enhancement**: Update tab schema
- **Enhancement**: Add navigation to WBE baseline detail

#### 2.1.3 New Routes

**`projects.$id.baselines.$baselineId.wbes.$wbeId.tsx`** (NEW)
- **Purpose**: WBE baseline detail page
- **Structure**: Similar to WBE detail but for baseline context
- **Tabs**: info, metrics, cost-elements, ai-assessment
- **Features**:
  - Shows WBE snapshot metrics
  - Lists cost elements for WBE in baseline
  - Navigation to cost element detail
  - Breadcrumb navigation

### 2.2 Data Structures Required

**API Response Types** (from generated client):
- `BaselineWBEPublic`: WBE snapshot with all EVM metrics
- `BaselineProjectPublic`: Project snapshot with all EVM metrics
- `BaselineWBEPublic[]`: List of WBE snapshots

**Component Props Interfaces**:
- `BaselineProjectSnapshotProps`
- `BaselineWBESnapshotProps`
- `BaselineMetricsSummaryProps`
- `BaselineWBESnapshotsTableProps`

**Status Indicator Types**:
- Reuse existing: `StatusIndicator` type from EarnedValueSummary
- Functions: `getCpiStatus()`, `getSpiStatus()`, `getTcpiStatus()`, `getVarianceStatus()`

### 2.3 Integration Points with Existing Code

1. **TanStack Query**:
   - Use `useQuery()` for data fetching
   - Query keys: `["baseline-project-snapshot", projectId, baselineId, controlDate]`
   - Query keys: `["baseline-wbe-snapshots", projectId, baselineId, controlDate]`
   - Query keys: `["baseline-wbe-snapshot", projectId, baselineId, wbeId, controlDate]`

2. **TanStack Router**:
   - Add new route for WBE baseline detail
   - Update search schema for new tabs
   - Use `navigate()` for programmatic navigation

3. **Chakra UI Components**:
   - `Tabs.Root`, `Tabs.List`, `Tabs.Trigger`, `Tabs.Content`
   - `Grid`, `Box`, `VStack`, `Flex` for layouts
   - `Heading`, `Text` for typography
   - `SkeletonText` for loading states

4. **Generated Client**:
   - `BaselineLogsService.getBaselineProjectSnapshot()`
   - `BaselineLogsService.getBaselineWbeSnapshots()`
   - `BaselineLogsService.getBaselineWbeSnapshotDetail()`

5. **Time Machine Context**:
   - Use `useTimeMachine()` hook
   - Include `controlDate` in query keys
   - Respect baseline_date for display

6. **Status Indicator Utilities**:
   - Extract status indicator functions to shared utility
   - Reuse in baseline components
   - Maintain consistency with operational views

### 2.4 Configuration or Settings Needed

- **No new configuration required**
- Uses existing TanStack Query configuration
- Uses existing Chakra UI theme
- Uses existing routing configuration

### 2.5 Security Considerations

1. **Authorization**:
   - Reuse existing authentication/authorization
   - API endpoints handle authorization
   - No additional client-side security needed

2. **Data Validation**:
   - TypeScript types ensure type safety
   - API response validation via generated client
   - Handle null/undefined values gracefully

3. **XSS Prevention**:
   - React automatically escapes content
   - No raw HTML rendering
   - Safe number/string formatting

## 3. TASK BREAKDOWN

### Phase 1: Core Baseline Metrics Display

**Task 1.1: Regenerate OpenAPI Client** [INTEGRATION]
- **Description**: Regenerate client to include new baseline snapshot endpoints
- **Acceptance Criteria**:
  - Client includes `getBaselineProjectSnapshot()`
  - Client includes `getBaselineWbeSnapshots()`
  - Client includes `getBaselineWbeSnapshotDetail()`
  - Types are generated correctly
- **Test**: Verify types exist and are importable
- **Files**: `frontend/src/client/sdk.gen.ts` (AUTO-GENERATED)
- **Estimated Time**: 5 minutes

**Task 1.2: Extract Status Indicator Utilities** [UNIT]
- **Description**: Extract status indicator functions to shared utility
- **Acceptance Criteria**:
  - Functions extracted to `frontend/src/utils/statusIndicators.ts`
  - All functions exported
  - Existing components updated to use shared utilities
  - No functionality changes
- **Test**: Verify existing components still work
- **Files**: `frontend/src/utils/statusIndicators.ts` (NEW), update existing components
- **Estimated Time**: 20 minutes

**Task 1.3: Create BaselineProjectSnapshot Component** [UNIT]
- **Description**: Create component to display project baseline snapshot
- **Acceptance Criteria**:
  - Component fetches project snapshot data
  - Displays all EVM metrics in card grid
  - Shows status indicators
  - Handles loading and error states
  - Matches EarnedValueSummary styling
- **Test**: Component renders correctly with mock data
- **Files**: `frontend/src/components/Projects/BaselineProjectSnapshot.tsx` (NEW)
- **Estimated Time**: 45 minutes

**Task 1.4: Create BaselineWBESnapshot Component** [UNIT]
- **Description**: Create component to display WBE baseline snapshot
- **Acceptance Criteria**:
  - Component fetches WBE snapshot data
  - Displays all EVM metrics in card grid
  - Shows status indicators
  - Handles loading and error states
- **Test**: Component renders correctly with mock data
- **Files**: `frontend/src/components/Projects/BaselineWBESnapshot.tsx` (NEW)
- **Estimated Time**: 45 minutes

**Task 1.5: Enhance BaselineSummary Component** [INTEGRATION]
- **Description**: Add EVM indices and project snapshot to BaselineSummary
- **Acceptance Criteria**:
  - Fetches project snapshot data
  - Displays CPI, SPI, TCPI, CV, SV
  - Shows status indicators
  - Maintains existing functionality
- **Test**: Component shows all metrics correctly
- **Files**: `frontend/src/components/Projects/BaselineSummary.tsx` (MODIFY)
- **Estimated Time**: 30 minutes

**Task 1.6: Add Project Metrics Tab to Baseline Detail** [INTEGRATION]
- **Description**: Add new tab showing project-level baseline metrics
- **Acceptance Criteria**:
  - New tab "Project Metrics" added
  - Tab shows BaselineProjectSnapshot component
  - Tab navigation works correctly
  - Search schema updated
- **Test**: Tab appears and displays metrics correctly
- **Files**: `frontend/src/routes/_layout/projects.$id.baselines.$baselineId.tsx` (MODIFY)
- **Estimated Time**: 20 minutes

### Phase 2: WBE-Level Display and Navigation

**Task 2.1: Create BaselineWBESnapshotsTable Component** [UNIT]
- **Description**: Create table component listing all WBE snapshots
- **Acceptance Criteria**:
  - Fetches list of WBE snapshots
  - Displays in DataTable format
  - Shows key metrics (BAC, EV, AC, CPI, SPI)
  - Links to WBE baseline detail
  - Sorting and filtering work
- **Test**: Table displays data correctly
- **Files**: `frontend/src/components/Projects/BaselineWBESnapshotsTable.tsx` (NEW)
- **Estimated Time**: 60 minutes

**Task 2.2: Add WBE Metrics Tab to Baseline Detail** [INTEGRATION]
- **Description**: Add tab showing WBE-level baseline metrics
- **Acceptance Criteria**:
  - New tab "WBE Metrics" added
  - Tab shows BaselineWBESnapshotsTable
  - Tab navigation works correctly
- **Test**: Tab appears and displays WBE snapshots
- **Files**: `frontend/src/routes/_layout/projects.$id.baselines.$baselineId.tsx` (MODIFY)
- **Estimated Time**: 15 minutes

**Task 2.3: Enhance BaselineCostElementsByWBETable** [INTEGRATION]
- **Description**: Add WBE snapshot metrics to accordion headers
- **Acceptance Criteria**:
  - Fetches WBE snapshot for each WBE
  - Displays key metrics in accordion header
  - Shows status indicators
  - Adds link to WBE baseline detail
- **Test**: Accordion headers show metrics and links work
- **Files**: `frontend/src/components/Projects/BaselineCostElementsByWBETable.tsx` (MODIFY)
- **Estimated Time**: 45 minutes

**Task 2.4: Create WBE Baseline Detail Route** [INTEGRATION]
- **Description**: Create nested route for WBE baseline detail page
- **Acceptance Criteria**:
  - Route: `/projects/$id/baselines/$baselineId/wbes/$wbeId`
  - Shows WBE snapshot metrics
  - Lists cost elements for WBE in baseline
  - Breadcrumb navigation works
  - Tabs: info, metrics, cost-elements, ai-assessment
- **Test**: Route works and displays correctly
- **Files**: `frontend/src/routes/_layout/projects.$id.baselines.$baselineId.wbes.$wbeId.tsx` (NEW)
- **Estimated Time**: 90 minutes

**Task 2.5: Add Navigation Links** [INTEGRATION]
- **Description**: Add links from baseline views to WBE baseline detail
- **Acceptance Criteria**:
  - Links in BaselineWBESnapshotsTable
  - Links in BaselineCostElementsByWBETable
  - Breadcrumb navigation works
  - Links preserve baseline context
- **Test**: All navigation links work correctly
- **Files**: Multiple files (MODIFY)
- **Estimated Time**: 30 minutes

### Phase 3: Testing and Polish

**Task 3.1: Component Tests** [UNIT]
- **Description**: Write tests for new components
- **Acceptance Criteria**:
  - Tests for BaselineProjectSnapshot
  - Tests for BaselineWBESnapshot
  - Tests for BaselineWBESnapshotsTable
  - Tests cover loading, error, and success states
- **Test**: All tests pass
- **Files**: Test files in `__tests__` folders (NEW)
- **Estimated Time**: 60 minutes

**Task 3.2: Integration Tests** [INTEGRATION]
- **Description**: Test navigation and data flow
- **Acceptance Criteria**:
  - Test baseline detail page navigation
  - Test WBE baseline detail page
  - Test data fetching and caching
  - Test error handling
- **Test**: All integration tests pass
- **Files**: Test files (NEW)
- **Estimated Time**: 45 minutes

**Task 3.3: E2E Tests** [E2E]
- **Description**: End-to-end tests for baseline UI
- **Acceptance Criteria**:
  - Test complete navigation flow
  - Test data display at all levels
  - Test responsive behavior
- **Test**: All E2E tests pass
- **Files**: Playwright tests (NEW)
- **Estimated Time**: 45 minutes

## 4. RISK ASSESSMENT

### 4.1 High Risk Areas

1. **Client Generation** (LOW)
   - **Risk**: OpenAPI client may not generate correctly
   - **Mitigation**: Verify OpenAPI spec is correct, test generation
   - **Verification**: Check generated types match API

2. **Data Fetching Performance** (LOW-MEDIUM)
   - **Risk**: Multiple API calls may be slow
   - **Mitigation**: Use TanStack Query caching, parallel queries
   - **Verification**: Monitor query performance

3. **Navigation State Management** (MEDIUM)
   - **Risk**: Complex nested routes may cause navigation issues
   - **Mitigation**: Follow existing patterns, test thoroughly
   - **Verification**: Test all navigation paths

4. **Component Consistency** (LOW)
   - **Risk**: New components may not match existing styling
   - **Mitigation**: Reuse existing components and patterns
   - **Verification**: Visual comparison with existing components

### 4.2 Dependencies on External Systems

- **Backend API**: Must be deployed with new endpoints
- **OpenAPI Spec**: Must be up-to-date for client generation
- **No external APIs**: All data from internal backend

### 4.3 Performance Considerations

1. **Query Optimization**:
   - Use parallel queries where possible
   - Leverage TanStack Query caching
   - Avoid unnecessary refetches

2. **Component Rendering**:
   - Use React.memo for expensive components
   - Lazy load components if needed
   - Optimize re-renders

3. **Large Data Sets**:
   - Use pagination for WBE lists
   - Virtual scrolling if needed
   - Limit initial data fetch

### 4.4 Backward Compatibility Requirements

1. **Existing Baselines**:
   - Must handle baselines without WBE/Project snapshots
   - Show appropriate message or fallback
   - Don't break existing baseline views

2. **API Compatibility**:
   - New endpoints are additive
   - Existing endpoints continue to work
   - No breaking changes

3. **Route Compatibility**:
   - New routes don't conflict with existing
   - Existing routes continue to work
   - URL structure is consistent

## 5. PHASE 2 TASKS (Future Enhancements)

### 5.1 Baseline Comparison Feature

**Description**: Allow users to compare two baselines side-by-side

**Tasks**:
- Create BaselineComparison component
- Add comparison selection UI
- Display metrics side-by-side
- Show variance between baselines
- Add comparison charts

**Estimated Complexity**: High
**Estimated Time**: 8-10 hours

### 5.2 Baseline Trend Charts

**Description**: Show baseline metrics trends over time

**Tasks**:
- Create BaselineTrendChart component
- Fetch multiple baseline snapshots
- Display trend lines for key metrics
- Add time range selector
- Integrate with existing chart components

**Estimated Complexity**: Medium
**Estimated Time**: 6-8 hours

### 5.3 Export Functionality

**Description**: Export baseline reports to PDF/Excel

**Tasks**:
- Add export button to baseline views
- Generate PDF reports
- Generate Excel reports
- Include charts and tables
- Customizable export formats

**Estimated Complexity**: Medium-High
**Estimated Time**: 8-10 hours

### 5.4 Baseline to Operational Navigation

**Description**: Easy navigation from baseline views to operational views

**Tasks**:
- Add "View Current" links
- Preserve context when switching
- Highlight differences
- Show comparison indicators

**Estimated Complexity**: Low-Medium
**Estimated Time**: 4-6 hours

### 5.5 Enhanced Visualizations

**Description**: Add more charts and visualizations for baseline data

**Tasks**:
- Performance index charts
- Variance analysis charts
- Budget vs Actual charts
- Forecast accuracy charts

**Estimated Complexity**: Medium
**Estimated Time**: 6-8 hours
