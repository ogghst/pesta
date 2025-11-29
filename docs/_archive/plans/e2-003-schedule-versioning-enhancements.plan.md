## Cost Element Schedule Versioning Enhancements Plan

### User Story
As a project controller, I need to review the full history of cost element schedules, ensure PV/EVM calculations always use the newest applicable registration, and confirm baselines capture the correct snapshot so that I can audit changes and trust project analytics.

### Implementation Steps
1. **Expand backend tests for schedule history retrieval**
   - **Acceptance Criteria**
     - A new test in `backend/tests/api/routes/test_cost_element_schedules.py` fails because the API does not yet expose a schedule history listing for a cost element.
     - Another test fails verifying baseline-linked schedules are excluded from the operational history response.
   - **Test-First Requirement**
     - Add `test_list_schedule_history_orders_by_registration_date` and `test_history_excludes_baseline_snapshots`, both initially failing.
   - **Expected Files**
     - `backend/tests/api/routes/test_cost_element_schedules.py`
   - **Dependencies**
     - None (kicks off the red phase).

2. **Implement backend history endpoint & data ordering**
   - **Acceptance Criteria**
     - New `GET /cost-element-schedules/history` endpoint returns all non-baseline schedule registrations sorted by `registration_date desc`, `created_at desc`.
     - Existing CRUD endpoints remain unchanged; PV/baseline selection logic continues to pass existing tests.
     - Newly added history tests pass without breaking current suite.
   - **Test-First Requirement**
     - Run the failing tests from Step 1; they must pass after implementation.
   - **Expected Files**
     - `backend/app/api/routes/cost_element_schedules.py`
     - `backend/app/models/cost_element_schedule.py` (schema for list response if required)
     - `backend/tests/api/routes/test_cost_element_schedules.py`
     - `frontend/src/client/sdk.gen.ts` (regenerated client)
   - **Dependencies**
     - Step 1.

3. **Add frontend Playwright coverage for schedule history UI**
   - **Acceptance Criteria**
     - New Playwright test fails because the UI does not yet render the history list.
   - **Test-First Requirement**
     - Extend `frontend/tests/project-cost-element-tabs.spec.ts` with an assertion that the edit modal shows prior schedule registrations once the section is implemented.
   - **Expected Files**
     - `frontend/tests/project-cost-element-tabs.spec.ts`
   - **Dependencies**
     - Step 2 (API contract must exist to power UI).

4. **Implement frontend schedule history display & wiring**
   - **Acceptance Criteria**
     - Edit Cost Element dialog renders a schedule history section listing registrations (registration date, date range, progression type, description).
     - Creating a new registration refreshes history; deleting latest registration updates list.
     - Playwright test from Step 3 passes; existing frontend tests remain green.
   - **Test-First Requirement**
     - Run Playwright test added in Step 3 (initially failing) and ensure it passes after UI changes.
   - **Expected Files**
     - `frontend/src/components/Projects/EditCostElement.tsx`
     - `frontend/src/components/Projects/ScheduleHistoryTable.tsx` (new)
     - `frontend/src/client/sdk.gen.ts`
     - Supporting style/components as needed (≤5 files target).
   - **Dependencies**
     - Step 3.

### TDD Discipline Rules
- Begin each step by introducing or running failing tests (red), follow with minimal implementation (green), and conclude with refactoring while keeping tests passing.
- No more than three attempts per step; if still red, pause and request guidance.
- Tests must assert functional behaviour (list ordering, exclusion rules, UI rendering), not just status codes.

### Process Checkpoints
- After **Step 2**, pause to confirm:
  - Should we continue with the plan as-is?
  - Have any assumptions been invalidated (e.g., performance concerns with history queries)?
  - Does the current API behaviour match expectations from Steps 1–2?
- After **Step 4**, re-evaluate overall scope compliance before any further enhancements.

### Scope Boundaries
- Focus strictly on cost element schedule history visibility and ensuring analytics logic remains correct.
- Do not modify PV or baseline calculation algorithms beyond ensuring they utilise existing helpers.
- Avoid introducing unrelated UI refactors or additional endpoints without explicit approval.

### Rollback Strategy
- Safe rollback points exist after each green phase:
  - Step 1 adds tests only—can revert the test commit if needed.
  - Step 2 backend changes can be reverted to restore prior API behaviour.
  - Step 3 introduces tests only—revert if UI plan changes.
  - Step 4 frontend implementation can be rolled back to previous UI while keeping history tests skipped if necessary.
- If backend history endpoint proves problematic, fallback approach is to keep documentation-only changes and surface history later via reporting endpoints.
