# E2E Test Issues Analysis

**Analysis Code:** 845713
**Date:** 2025-11-29
**Analyst:** AI Assistant
**Status:** In Progress

## Executive Summary

This analysis documents issues identified while running pending E2E tests from the frontend test suite. The analysis covers 6 pending test files and identifies specific failures, potential root causes, and recommended fixes.

## Test Execution Summary

### Tests Analyzed

1. **reset-password.spec.ts** (7 tests) - Partially executed
2. **user-settings.spec.ts** - Not yet executed (hanging/timeout)
3. **forecast-crud.spec.ts** (6 tests) - Failed on first test
4. **project-performance-dashboard.spec.ts** (1 test) - Not yet executed
5. **project-cost-element-tabs.spec.ts** (9 tests) - Not yet executed
6. **time-machine.spec.ts** - Not yet executed

## Issues Identified

### 1. forecast-crud.spec.ts - "Forecasts" Tab Not Found

**Status:** ❌ Failing
**Test:** `should create a forecast`
**Error:**
```
Error: page.waitForSelector: Test ended.
Call log:
  - waiting for locator('text="Forecasts"') to be visible
```

**Root Cause Analysis:**
- The test navigates to: `/projects/${projectId}/wbes/${wbeId}/cost-elements/${costElementId}?view=forecasts`
- The test expects to find text "Forecasts" within 10 seconds
- The selector `'text="Forecasts"'` should match either:
  - The tab trigger: `<Tabs.Trigger value="forecasts">Forecasts</Tabs.Trigger>`
  - The heading in ForecastsTable: `<Heading size="md">Forecasts</Heading>`

**Potential Issues:**
1. **Timing Issue**: The page may not be fully loaded when the selector is checked
2. **Tab Not Activated**: The `view=forecasts` parameter may not be activating the correct tab
3. **Component Not Rendered**: The ForecastsTable component may not be rendering due to missing data or API errors
4. **Selector Specificity**: The text selector may be too generic and matching something else

**Recommended Fixes:**
1. Use a more specific selector: `page.getByRole("heading", { name: "Forecasts" })` or `page.getByRole("tab", { name: "Forecasts" })`
2. Wait for the tab content to be visible instead of just the text
3. Add explicit wait for the forecasts tab to be active: `await page.waitForURL(/view=forecasts/)`
4. Check if the cost element data is loaded before checking for the tab
5. Increase timeout or add retry logic

**Code Location:**
- Test: `frontend/tests/forecast-crud.spec.ts:131`
- Component: `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.cost-elements.$costElementId.tsx:252`
- Table: `frontend/src/components/Projects/ForecastsTable.tsx:60`

### 2. reset-password.spec.ts - Email Tests Hanging

**Status:** ⏳ Partial (First 3 tests pass, email tests hang)
**Tests Passing:**
- ✅ Password Recovery title is visible
- ✅ Input is visible, empty and editable
- ✅ Continue button is visible

**Tests Hanging:**
- ⏳ User can reset password successfully using the link
- ⏳ Weak new password validation

**Root Cause Analysis:**
- Tests that use `findLastEmail` from `utils/mailcatcher.ts` are hanging
- The `findLastEmail` function has a 5-second timeout but appears to be waiting indefinitely
- Mailcatcher service is running (confirmed via `docker ps`)

**Potential Issues:**
1. **Email Not Being Sent**: Backend may not be sending emails to mailcatcher
2. **Mailcatcher API Issue**: The mailcatcher API endpoint may not be responding
3. **Email Filter Issue**: The filter function may not be matching emails correctly
4. **Race Condition**: Email may arrive after the timeout, or the polling loop may have issues
5. **Environment Variable**: `MAILCATCHER_HOST` may not be set correctly

**Recommended Fixes:**
1. Verify `MAILCATCHER_HOST` environment variable is set: `http://localhost:1080`
2. Add logging to `findLastEmail` to debug the polling loop
3. Check mailcatcher API directly: `curl http://localhost:1080/messages`
4. Verify backend email configuration is pointing to mailcatcher
5. Increase timeout for email tests (currently 5 seconds)
6. Add explicit wait after clicking "Continue" button before checking for email

**Code Location:**
- Test: `frontend/tests/reset-password.spec.ts:47-51, 102-106`
- Utility: `frontend/tests/utils/mailcatcher.ts:33-62`

### 3. user-settings.spec.ts - Test Execution Hanging

**Status:** ⏳ Not Executed (Hanging/Timeout)
**Issue:** Test execution appears to hang or timeout before completing

**Potential Issues:**
1. **Authentication Issues**: Tests may be failing during setup/auth
2. **Component Loading**: UI components may not be loading correctly
3. **API Timeouts**: Backend API calls may be timing out
4. **Test Data Issues**: Seeded test data may not be available

**Recommended Investigation:**
1. Run individual tests within the file to isolate the issue
2. Check if authentication setup is working correctly
3. Verify backend services are running and responsive
4. Check for console errors in browser during test execution
5. Review test dependencies and setup hooks

### 4. project-performance-dashboard.spec.ts - Not Yet Tested

**Status:** ⏳ Pending
**Potential Issues to Watch For:**
- Similar to forecast tests, may have selector/timing issues
- Dashboard data loading may be slow
- Multiple API calls may cause race conditions

### 5. project-cost-element-tabs.spec.ts - Not Yet Tested

**Status:** ⏳ Pending
**Potential Issues to Watch For:**
- Tab navigation issues
- Baseline modal interactions
- Schedule history display
- URL parameter mapping (tab=summary, tab=cost-summary)

### 6. time-machine.spec.ts - Not Yet Tested

**Status:** ⏳ Pending
**Potential Issues to Watch For:**
- Time machine input interaction
- Date filtering logic
- WBE visibility based on creation date

## Common Patterns and Recommendations

### Selector Issues

**Problem:** Tests using generic text selectors may fail due to timing or specificity issues.

**Solution:**
- Prefer role-based selectors: `page.getByRole("heading", { name: "Forecasts" })`
- Use test IDs where available: `page.getByTestId("forecasts-tab")`
- Wait for specific elements rather than generic text

### Timing Issues

**Problem:** Tests may fail due to race conditions or slow loading.

**Solution:**
- Use explicit waits: `await page.waitForURL(/view=forecasts/)`
- Wait for network idle: `await page.waitForLoadState("networkidle")`
- Increase timeouts for slow operations
- Use `waitForSelector` with appropriate options

### Email Testing

**Problem:** Email tests are unreliable and may hang.

**Solution:**
- Verify mailcatcher is accessible before tests
- Add retry logic with exponential backoff
- Log email polling attempts for debugging
- Consider mocking email service for faster tests

### Test Data Setup

**Problem:** Tests may fail if seeded data is not available or incorrect.

**Solution:**
- Verify `beforeAll` hooks complete successfully
- Add assertions to verify test data exists
- Use unique identifiers (timestamps) to avoid conflicts
- Clean up test data after tests complete

## Next Steps

1. **Fix forecast-crud.spec.ts**:
   - Update selector to use role-based approach
   - Add explicit waits for tab activation
   - Verify cost element data is loaded

2. **Fix reset-password.spec.ts**:
   - Debug email polling mechanism
   - Verify mailcatcher connectivity
   - Add logging for email retrieval

3. **Investigate user-settings.spec.ts**:
   - Run individual tests to isolate issues
   - Check authentication flow
   - Verify component rendering

4. **Run Remaining Tests**:
   - Execute project-performance-dashboard.spec.ts
   - Execute project-cost-element-tabs.spec.ts
   - Execute time-machine.spec.ts

5. **Update Test Log**:
   - Document all findings in `docs/frontend-e2e-test-log.md`
   - Update test statuses
   - Record fixes applied

## Testing Infrastructure

### Prerequisites Verified
- ✅ Mailcatcher service running (port 1080)
- ✅ Database service running
- ⚠️ Backend service status unknown (should verify)

### Environment Variables Required
- `FIRST_SUPERUSER` - Set
- `FIRST_SUPERUSER_PASSWORD` - Set
- `VITE_API_URL` - Should be `http://localhost:8010`
- `MAILCATCHER_HOST` - Should be `http://localhost:1080`

### Test Execution Command
```bash
cd frontend
eval "$(fnm env)"
fnm use 22
npx playwright test tests/<test-file>.spec.ts --reporter=list --workers=1
```

## Conclusion

The main issues identified are:
1. **Selector specificity** in forecast tests
2. **Email polling reliability** in password reset tests
3. **Test execution hanging** in user settings tests

These issues are fixable with targeted changes to selectors, timing, and error handling. The test infrastructure appears to be set up correctly, but individual tests need refinement.
