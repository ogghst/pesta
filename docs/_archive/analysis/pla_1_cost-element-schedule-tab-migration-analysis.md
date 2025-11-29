# PLA-1: Cost Element Schedule CRUD Migration to Tab - High-Level Analysis

**Feature:** Move cost element schedule CRUD operations from the cost element edit form to a dedicated tab in the cost element detail page, following the same pattern as cost registrations.

**User Story:**
> As a project manager, I want to manage cost element schedules in a dedicated tab (similar to cost registrations) so that schedule management is separated from basic cost element information and provides better space for viewing schedule history and managing multiple schedule registrations.

---

## 1. CODEBASE PATTERN ANALYSIS

### 1.1 Reference Implementation: Cost Registrations Tab

**Location:** `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.cost-elements.$costElementId.tsx`

**Pattern Structure:**
- Tab-based navigation using Chakra UI `Tabs.Root` component
- Tab state managed via TanStack Router search params (`view` parameter)
- Each tab renders a dedicated component (e.g., `CostRegistrationsTable`)
- Tab options defined as const array with TypeScript type safety

**Key Components:**
1. **Table Component:** `CostRegistrationsTable.tsx`
   - Uses `DataTable` component for display
   - Pagination via TanStack Query with page state
   - Actions column with Edit/Delete buttons
   - Add button in header

2. **CRUD Components:**
   - `AddCostRegistration.tsx` - Dialog-based form for creation
   - `EditCostRegistration.tsx` - Dialog-based form for updates
   - `DeleteCostRegistration.tsx` - Confirmation dialog for deletion

**Architectural Layers:**
- **Routing:** TanStack Router with file-based routing
- **State Management:** TanStack Query for server state, React state for UI
- **Forms:** React Hook Form with validation
- **UI Components:** Chakra UI v3 (Dialog, Table, Form fields)
- **Data Display:** Custom `DataTable` component wrapping TanStack Table

### 1.2 Current Implementation: Schedule in Edit Form

**Location:** `frontend/src/components/Projects/EditCostElement.tsx`

**Current Structure:**
- Schedule section embedded within cost element edit dialog (lines 541-709)
- Schedule form fields mixed with cost element fields
- Schedule history table displayed inline
- Schedule operations (create/update/delete) coupled with cost element save operation
- Single form submission handles both cost element and schedule updates

**Key Dependencies:**
- `ScheduleHistoryTable.tsx` - Displays schedule history (already exists)
- `CostElementSchedulesService` - API client for schedule operations
- React Hook Form with separate schedule form state

### 1.3 Established Patterns

**Namespace/Interface Patterns:**
- Service classes: `{Resource}SchedulesService` (e.g., `CostElementSchedulesService`)
- Public types: `{Resource}SchedulePublic` (e.g., `CostElementSchedulePublic`)
- Update types: `{Resource}ScheduleUpdate` (e.g., `CostElementScheduleUpdate`)
- Base types: `{Resource}ScheduleBase` (e.g., `CostElementScheduleBase`)

**Component Patterns:**
- Table components: `{Resource}Table.tsx` in `components/Projects/`
- Add components: `Add{Resource}.tsx` with dialog trigger
- Edit components: `Edit{Resource}.tsx` with dialog trigger
- Delete components: `Delete{Resource}.tsx` with confirmation dialog

**Query Key Patterns:**
- Single resource: `["cost-element-schedule", costElementId]`
- History: `["cost-element-schedule-history", costElementId]`
- Lists: `["cost-registrations", { costElementId, page }]`

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### 2.1 Files Requiring Modification

**Route File:**
- `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.cost-elements.$costElementId.tsx`
  - Add "schedule" to `COST_ELEMENT_VIEW_OPTIONS` array
  - Add new tab trigger: `<Tabs.Trigger value="schedule">Schedule</Tabs.Trigger>`
  - Add new tab content: `<Tabs.Content value="schedule">` with `CostElementSchedulesTable` component

**Edit Form File:**
- `frontend/src/components/Projects/EditCostElement.tsx`
  - **Remove:** Schedule section (lines 541-709)
  - **Remove:** Schedule-related state, queries, and mutations
  - **Remove:** Schedule form handling from `onSubmit`
  - **Keep:** Cost element form fields and validation only
  - **Simplify:** Form submission to only handle cost element updates

### 2.2 Files to Create

**New Table Component:**
- `frontend/src/components/Projects/CostElementSchedulesTable.tsx`
  - Similar structure to `CostRegistrationsTable.tsx`
  - Uses `DataTable` component
  - Displays schedule history with columns: registration_date, start_date, end_date, progression_type, description
  - Actions column with Edit/Delete buttons
  - Add button in header

**New CRUD Components:**
- `frontend/src/components/Projects/AddCostElementSchedule.tsx`
  - Dialog-based form following `AddCostRegistration.tsx` pattern
  - Fields: registration_date, start_date, end_date, progression_type, description, notes
  - Validation: end_date >= start_date
  - Uses `CostElementSchedulesService.createSchedule()`

- `frontend/src/components/Projects/EditCostElementSchedule.tsx`
  - Dialog-based form following `EditCostRegistration.tsx` pattern
  - Pre-populated with existing schedule data
  - Uses `CostElementSchedulesService.updateSchedule()`

- `frontend/src/components/Projects/DeleteCostElementSchedule.tsx`
  - Confirmation dialog following `DeleteCostRegistration.tsx` pattern
  - Uses `CostElementSchedulesService.deleteSchedule()`

### 2.3 System Dependencies

**Backend API (Already Exists):**
- `GET /api/v1/cost-element-schedules/?cost_element_id={id}` - Get latest schedule
- `GET /api/v1/cost-element-schedules/history?cost_element_id={id}` - Get full history
- `POST /api/v1/cost-element-schedules/?cost_element_id={id}` - Create schedule
- `PUT /api/v1/cost-element-schedules/{id}` - Update schedule
- `DELETE /api/v1/cost-element-schedules/{id}` - Delete schedule

**Frontend Client (Already Generated):**
- `CostElementSchedulesService` class with all CRUD methods
- Type definitions: `CostElementSchedulePublic`, `CostElementScheduleBase`, `CostElementScheduleUpdate`

**Configuration:**
- No new configuration required
- Uses existing TanStack Router search param validation
- Uses existing query key invalidation patterns

---

## 3. ABSTRACTION INVENTORY

### 3.1 Reusable Components

**DataTable Component:**
- Location: `frontend/src/components/DataTable/DataTable.tsx`
- Usage: Wrap schedule history data with column definitions
- Supports: Pagination, sorting, filtering, column visibility, resizing

**Dialog Components:**
- Location: `frontend/src/components/ui/dialog`
- Components: `DialogRoot`, `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogBody`, `DialogFooter`, `DialogActionTrigger`, `DialogCloseTrigger`
- Usage: All CRUD dialogs use this pattern

**Form Components:**
- Location: `frontend/src/components/ui/field`
- Component: `Field` - Wraps label, input, and error display
- Usage: All form fields in Add/Edit components

**Toast Notifications:**
- Hook: `useCustomToast` from `@/hooks/useCustomToast`
- Methods: `showSuccessToast()`, `showErrorToast()`
- Usage: Success/error feedback in all mutations

### 3.2 Utility Functions

**Error Handling:**
- Function: `handleError()` from `@/utils`
- Usage: Standardized API error handling in mutation `onError` callbacks

**Date Formatting:**
- Library: `date-fns` (already used in `ScheduleHistoryTable.tsx`)
- Function: `format()` for date display
- Usage: Format dates in table cells and forms

### 3.3 Hooks and Patterns

**TanStack Query Patterns:**
- `useQuery` for data fetching with query keys
- `useMutation` for create/update/delete operations
- `queryClient.invalidateQueries()` for cache invalidation
- Pattern: Invalidate both specific and list queries after mutations

**React Hook Form Patterns:**
- `useForm` with `mode: "onBlur"` for validation
- `Controller` for select/checkbox inputs
- `register` for text/date inputs
- Form validation with custom rules

**State Management:**
- Component-level state with `useState` for dialog open/close
- URL state via TanStack Router search params for tab navigation
- Server state via TanStack Query

### 3.4 Test Utilities

**Existing Test Patterns:**
- Location: `frontend/tests/project-cost-element-tabs.spec.ts`
- Pattern: E2E tests using Playwright
- Can extend: Add tests for schedule tab navigation and CRUD operations

---

## 4. ALTERNATIVE APPROACHES

### 4.1 Approach 1: Dedicated Schedule Tab (RECOMMENDED)

**Description:**
Create a new "Schedule" tab in the cost element detail page, following the exact pattern used for cost registrations. Extract schedule CRUD operations into separate components and display schedule history in a table format.

**Implementation:**
- Add "schedule" to tab options in cost element detail route
- Create `CostElementSchedulesTable` component using `DataTable`
- Create Add/Edit/Delete schedule components as dialogs
- Remove schedule section from `EditCostElement` form
- Schedule operations become independent of cost element updates

**Pros:**
- ✅ Follows established pattern (cost registrations)
- ✅ Consistent user experience across tabs
- ✅ Better separation of concerns (schedule vs. cost element data)
- ✅ More space for schedule history display
- ✅ Independent schedule management (no need to open edit form)
- ✅ Aligns with existing architecture patterns
- ✅ Easier to test and maintain

**Cons:**
- ⚠️ Requires creating 4 new component files
- ⚠️ Requires modifying existing `EditCostElement` component
- ⚠️ Slightly more code to maintain

**Alignment with Architecture:**
- ✅ Matches existing tab structure
- ✅ Uses existing `DataTable` component
- ✅ Follows established CRUD component patterns
- ✅ Uses same routing and state management patterns

**Estimated Complexity:** Medium
- Frontend: New tab + 4 new components + modify edit form (8-10 hours)
- Testing: E2E tests for tab and CRUD operations (2-3 hours)
- Total: 10-13 hours

**Risk Factors:**
- Low risk - well-established patterns
- Need to ensure schedule operations still work correctly after extraction
- Need to handle edge case: cost element without schedule

### 4.2 Approach 2: Keep Schedule in Edit Form, Add Read-Only Tab

**Description:**
Keep schedule CRUD in the edit form but add a read-only "Schedule" tab that displays schedule history using `ScheduleHistoryTable` component.

**Implementation:**
- Add "schedule" tab with read-only history display
- Keep schedule CRUD in `EditCostElement` form
- Tab only shows history, no actions

**Pros:**
- ✅ Minimal changes to existing code
- ✅ Schedule history visible without opening edit form
- ✅ Less code duplication

**Cons:**
- ❌ Inconsistent with cost registrations pattern (they have full CRUD in tab)
- ❌ Schedule management still requires opening edit form
- ❌ Doesn't fully address the requirement (CRUD should be in tab)
- ❌ Mixed responsibilities (read in tab, write in form)

**Alignment with Architecture:**
- ⚠️ Partially aligns (read-only tab exists, but CRUD pattern differs)
- ⚠️ Creates inconsistency with cost registrations

**Estimated Complexity:** Low
- Frontend: Add tab + display component (2-3 hours)

**Risk Factors:**
- Medium risk - creates pattern inconsistency
- Doesn't fully solve the problem

### 4.3 Approach 3: Modal-Based Schedule Management

**Description:**
Keep schedule in a separate modal dialog that can be opened from the cost element detail page, independent of the edit form.

**Implementation:**
- Add "Manage Schedule" button in cost element detail page
- Open modal with schedule CRUD operations
- Remove schedule from edit form

**Pros:**
- ✅ Separates schedule from cost element edit
- ✅ Can be accessed without editing cost element
- ✅ Modal provides focused interface

**Cons:**
- ❌ Doesn't follow tab pattern (inconsistent with cost registrations)
- ❌ Requires additional navigation step
- ❌ Less discoverable than tab-based approach
- ❌ Doesn't match existing architecture patterns

**Alignment with Architecture:**
- ❌ Doesn't match tab-based pattern used elsewhere
- ❌ Creates new pattern instead of reusing existing one

**Estimated Complexity:** Medium
- Frontend: Modal component + button integration (6-8 hours)

**Risk Factors:**
- Medium risk - introduces new pattern
- Lower user discoverability

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### 5.1 Architectural Principles

**Follows:**
- ✅ **Separation of Concerns:** Schedule management separated from cost element editing
- ✅ **Consistency:** Matches existing tab-based CRUD pattern (cost registrations)
- ✅ **Reusability:** Uses existing `DataTable`, dialog, and form components
- ✅ **Single Responsibility:** Each component has a clear, focused purpose
- ✅ **DRY (Don't Repeat Yourself):** Reuses established patterns and abstractions

**Potential Violations:**
- None identified - approach follows established patterns

### 5.2 Future Maintenance Burden

**Positive Impacts:**
- ✅ Schedule management becomes independent, easier to modify
- ✅ Consistent patterns make onboarding easier
- ✅ Tab-based approach scales well for additional features

**Potential Concerns:**
- ⚠️ More component files to maintain (4 new components)
- ⚠️ Need to keep schedule tab in sync with cost registrations pattern if pattern evolves

**Mitigation:**
- Follow established patterns closely to minimize divergence
- Document pattern decisions for future reference

### 5.3 Testing Challenges

**Unit Testing:**
- Test each CRUD component independently
- Test form validation (date validation, required fields)
- Test error handling in mutations

**Integration Testing:**
- Test tab navigation and state persistence
- Test table pagination and data display
- Test query invalidation after mutations

**E2E Testing:**
- Test full CRUD workflow in schedule tab
- Test navigation between tabs
- Test edge cases (no schedule, schedule history)

**Existing Test Infrastructure:**
- Playwright tests in `frontend/tests/`
- Can extend `project-cost-element-tabs.spec.ts` with schedule tab tests

---

## 6. AMBIGUITIES AND CLARIFICATIONS NEEDED

### 6.1 Schedule Display in Tab

**Question:** Should the schedule tab show:
- Option A: Full history table (all schedule registrations) with latest highlighted?
- Option B: Latest schedule with history below?
- Option C: Only history table (no "current" schedule display)?

**Recommendation:** Option A - Full history table (matches cost registrations pattern where all items are shown in table)

### 6.2 Schedule Creation Flow

**Question:** When creating the first schedule for a cost element:
- Should "Add Schedule" button be always visible?
- Should there be a message when no schedule exists?

**Recommendation:** Always show "Add Schedule" button (matches cost registrations pattern)

### 6.3 Edit Form Behavior

**Question:** After removing schedule from edit form:
- Should edit form still show schedule read-only info?
- Or completely remove schedule from edit form?

**Recommendation:** Completely remove schedule from edit form (clean separation)

### 6.4 Default Tab

**Question:** Should "schedule" tab be the default tab, or keep "cost-registrations" as default?

**Recommendation:** Keep "cost-registrations" as default (no change to existing behavior)

---

## 7. RISKS AND UNKNOWN FACTORS

### 7.1 Identified Risks

**Low Risk:**
- Pattern is well-established (cost registrations)
- Backend API already exists and is tested
- No breaking changes to existing functionality

**Medium Risk:**
- Need to ensure schedule operations still work correctly after extraction
- Need to handle edge cases (cost element without schedule)
- Need to verify query invalidation works correctly

**Mitigation Strategies:**
- Follow cost registrations pattern exactly
- Comprehensive testing of CRUD operations
- Test edge cases (no schedule, single schedule, multiple schedules)

### 7.2 Unknown Factors

**Data Migration:**
- No data migration needed (schedule data already exists)
- No schema changes required

**Performance:**
- Schedule history query may need pagination if many registrations exist
- Current implementation doesn't paginate history - may need to add if performance issues arise

**User Experience:**
- Need to verify users understand schedule is now in separate tab
- May need to add breadcrumb or navigation hint

---

## 8. SUMMARY

### 8.1 Feature Summary

Move cost element schedule CRUD operations from the embedded form section in `EditCostElement` dialog to a dedicated "Schedule" tab in the cost element detail page, following the exact pattern established by the cost registrations tab.

### 8.2 Key Decisions

1. **Approach:** Dedicated Schedule tab (Approach 1) - recommended
2. **Pattern:** Follow cost registrations pattern exactly
3. **Components:** Create 4 new components (Table, Add, Edit, Delete)
4. **Modifications:** Remove schedule section from `EditCostElement` form

### 8.3 Next Steps

1. Wait for user feedback on ambiguities (section 6)
2. Confirm approach selection
3. Proceed to detailed implementation plan
4. Create failing tests first (TDD approach)
5. Implement incrementally with small commits

---

## 9. REFERENCES

**Key Files:**
- `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.cost-elements.$costElementId.tsx` - Cost element detail page with tabs
- `frontend/src/components/Projects/CostRegistrationsTable.tsx` - Reference table component
- `frontend/src/components/Projects/AddCostRegistration.tsx` - Reference add component
- `frontend/src/components/Projects/EditCostRegistration.tsx` - Reference edit component
- `frontend/src/components/Projects/DeleteCostRegistration.tsx` - Reference delete component
- `frontend/src/components/Projects/EditCostElement.tsx` - Current schedule implementation
- `frontend/src/components/Projects/ScheduleHistoryTable.tsx` - Existing history display
- `backend/app/api/routes/cost_element_schedules.py` - Backend API

**Related Analysis:**
- `docs/analysis/e3-001-cost-registration-interface-analysis.md` - Cost registrations tab analysis
- `docs/plans/e2-003-cost-element-schedule-management.plan.md` - Original schedule implementation plan
