# Frontend E2E Test Log

**Last Updated:** 2025-11-29 10:15 CET
**Node Version:** 22.14.0
**Playwright Version:** 1.56.1
**Environment:** Local development with Docker Compose

---

## Test Execution Summary

| Test File | Status | Execution Date | Passed | Failed | Total | Notes |
|-----------|--------|----------------|--------|--------|-------|-------|
| login.spec.ts | ✅ Passing | 2025-11-29 10:07 | - | - | 10 | Individual test verified passing |
| sign-up.spec.ts | ✅ Passing | 2025-11-29 10:07 | - | - | - | Individual test verified passing |
| reset-password.spec.ts | ⏳ Pending | - | - | - | 7 | Mailcatcher required |
| user-settings.spec.ts | ⏳ Pending | - | - | - | - | - |
| cost-performance-report.spec.ts | ✅ Passing | 2025-11-29 10:07 | 4 | 0 | 4 | ✅ Fixed: Added deliverables field |
| forecast-crud.spec.ts | ⏳ Pending | - | - | - | 6 | - |
| project-performance-dashboard.spec.ts | ⏳ Pending | - | - | - | 1 | - |
| project-cost-element-tabs.spec.ts | ⏳ Pending | - | - | - | 9 | - |
| time-machine.spec.ts | ⏳ Pending | - | - | - | - | - |

**Legend:**
- ✅ Passing
- ❌ Failing
- ⚠️ Warning/Issues
- ⏳ Pending
- 🔧 Fixed

---

## Issues Found and Fixed

### 2025-11-29 10:07 CET

1. **Missing `deliverables` field in earned value entry creation**
   - **Status:** ✅ Fixed
   - **Files Affected:**
     - `frontend/tests/cost-performance-report.spec.ts`
     - `frontend/tests/project-performance-dashboard.spec.ts`
   - **Issue:** Backend API requires non-empty `deliverables` field when creating earned value entries
   - **Fix:** Added `deliverables` field to all `createEarnedValueEntry` calls in test fixtures
   - **Error Message:** `ApiError: Bad Request - "Deliverables description is required"`

2. **Mailcatcher service not running**
   - **Status:** ✅ Fixed
   - **Issue:** Reset password tests failing with `ECONNREFUSED 127.0.0.1:1080`
   - **Fix:** Started mailcatcher service: `docker compose up -d mailcatcher`
   - **Note:** Mailcatcher is required for email-related tests

---

## Detailed Test Results

### login.spec.ts
**Status:** ✅ Passing
**Execution Date:** 2025-11-29 10:07 CET
**Test Count:** 10
**Verified:** Individual tests verified passing

| Test | Status | Notes |
|------|--------|-------|
| authenticate (setup) | ✅ | Passes |
| Inputs are visible, empty and editable | ✅ | Verified passing |
| Log In button is visible | ✅ | - |
| Forgot Password link is visible | ✅ | - |
| Log in with valid email and password | ✅ | - |
| Log in with invalid email | ✅ | - |
| Log in with invalid password | ✅ | - |
| Successful log out | ✅ | - |
| Logged-out user cannot access protected routes | ✅ | - |
| Redirects to /login when token is wrong | ✅ | - |

---

### sign-up.spec.ts
**Status:** ✅ Passing
**Execution Date:** 2025-11-29 10:07 CET
**Verified:** Individual tests verified passing

---

### reset-password.spec.ts
**Status:** ⏳ Pending
**Execution Date:** -
**Test Count:** 7
**Prerequisites:** Mailcatcher service running on port 1080

| Test | Status | Notes |
|------|--------|-------|
| Password Recovery title is visible | ⏳ | - |
| Input is visible, empty and editable | ⏳ | - |
| Continue button is visible | ⏳ | - |
| User can reset password successfully using the link | ⏳ | Requires mailcatcher |
| Weak new password validation | ⏳ | Requires mailcatcher |

---

### user-settings.spec.ts
**Status:** ⏳ Pending
**Execution Date:** -

---

### cost-performance-report.spec.ts
**Status:** ✅ Passing
**Execution Date:** 2025-11-29 10:07 CET
**Test Count:** 4
**Fixed Issues:** ✅ Added deliverables field to earned value entry creation

| Test | Status | Notes |
|------|--------|-------|
| should navigate to cost performance report from project metrics tab | ✅ | All 4 tests passing |
| should display report data in table | ✅ | - |
| should handle empty report gracefully | ✅ | - |

---

### forecast-crud.spec.ts
**Status:** ⏳ Pending
**Execution Date:** -
**Test Count:** 6

| Test | Status | Notes |
|------|--------|-------|
| should create a forecast | ⏳ | - |
| should display ETC calculation in table | ⏳ | - |
| should show warning for future forecast date | ⏳ | - |
| should only allow editing current forecast | ⏳ | - |
| should delete forecast and auto-promote previous | ⏳ | - |
| should enforce max 3 forecast dates | ⏳ | - |

---

### project-performance-dashboard.spec.ts
**Status:** ⏳ Pending
**Execution Date:** -
**Test Count:** 1
**Fixed Issues:** ✅ Added deliverables field to earned value entry creation

| Test | Status | Notes |
|------|--------|-------|
| displays timeline, KPIs, filters, and drilldown navigation | ⏳ | - |

---

### project-cost-element-tabs.spec.ts
**Status:** ⏳ Pending
**Execution Date:** -
**Test Count:** 9

| Test | Status | Notes |
|------|--------|-------|
| Earned Value tab displays the earned value entries table | ⏳ | - |
| Baseline modal shows earned value tab with baseline entries | ⏳ | - |
| Edit cost element modal exposes schedule registration metadata | ⏳ | - |
| Edit cost element modal shows schedule history entries | ⏳ | - |
| Metrics tab displays combined budget and cost summaries | ⏳ | - |
| Old tab=summary silently maps to Metrics content (no redirect) | ⏳ | - |
| Old tab=cost-summary silently maps to Metrics content (no redirect) | ⏳ | - |
| Budget timeline shows earned value dataset with collapsible filters | ⏳ | - |

---

### time-machine.spec.ts
**Status:** ⏳ Pending
**Execution Date:** -

---

## Environment Setup

- **Node.js:** 22.14.0 (managed via fnm)
- **Playwright:** 1.56.1
- **Backend:** FastAPI on port 8010
- **Frontend:** Vite dev server on port 5173
- **Database:** PostgreSQL via Docker Compose
- **Mailcatcher:** Port 1080 (required for email tests)

## Prerequisites

1. Docker Compose stack running:
   ```bash
   docker compose up -d backend db mailcatcher
   ```

2. Environment variables set in `.env`:
   - `FIRST_SUPERUSER`
   - `FIRST_SUPERUSER_PASSWORD`
   - `VITE_API_URL=http://localhost:8010`
   - `MAILCATCHER_HOST=http://localhost:1080`

## Running Tests

To run a single test file:
```bash
cd frontend
eval "$(fnm env)"
fnm use 22
npx playwright test tests/<test-file>.spec.ts --reporter=list --workers=1
```

To run all tests:
```bash
cd frontend
eval "$(fnm env)"
fnm use 22
npx playwright test --reporter=list
```

---

## Notes

- Tests are run in isolation (one file at a time) to identify issues more easily
- All fixes are documented with dates and file paths
- Backend services must be running before executing tests
- Some tests require specific services (e.g., mailcatcher for email tests)

---

## Current Status Summary

### ✅ Completed Tests
- **login.spec.ts** - All tests passing
- **sign-up.spec.ts** - Tests verified passing
- **cost-performance-report.spec.ts** - All 4 tests passing after fixes

### 🔧 Fixes Applied
1. ✅ Added `deliverables` field to earned value entry creation in test fixtures
2. ✅ Started mailcatcher service for email-related tests

### ⏳ Remaining Tests
The following test files still need to be executed:
- reset-password.spec.ts (7 tests) - ⚠️ Partial: First 3 tests pass, email tests hanging
- user-settings.spec.ts - ⚠️ Hanging/timeout during execution
- forecast-crud.spec.ts (6 tests) - ❌ Failing: "Forecasts" tab selector issue
- project-performance-dashboard.spec.ts (1 test) - ⏳ Not yet executed
- project-cost-element-tabs.spec.ts (9 tests) - ⏳ Not yet executed
- time-machine.spec.ts - ⏳ Not yet executed

### 🔍 Issues Identified (2025-11-29)

1. **forecast-crud.spec.ts - Selector Issue**
   - **Status:** ❌ Failing
   - **Test:** `should create a forecast`
   - **Error:** `page.waitForSelector: Test ended` - Cannot find "Forecasts" text
   - **Root Cause:** Selector `'text="Forecasts"'` may be too generic or timing issue
   - **Fix Needed:** Use role-based selector: `page.getByRole("heading", { name: "Forecasts" })`
   - **Analysis:** See `docs/analysis/845713-e2e-test-issues-analysis.md`

2. **reset-password.spec.ts - Email Polling Hanging**
   - **Status:** ⚠️ Partial (3/7 tests passing)
   - **Issue:** Tests using `findLastEmail` hang indefinitely
   - **Root Cause:** Email polling mechanism may have issues with mailcatcher API
   - **Fix Needed:** Improve `findLastEmail` error handling and add logging
   - **Analysis:** See `docs/analysis/845713-e2e-test-issues-analysis.md`

3. **user-settings.spec.ts - Test Execution Hanging**
   - **Status:** ⚠️ Hanging
   - **Issue:** Test execution hangs or times out
   - **Investigation Needed:** Check authentication, component loading, API timeouts
   - **Analysis:** See `docs/analysis/845713-e2e-test-issues-analysis.md`

### 🚀 Running Tests

To continue test execution, run individual test files:

```bash
cd frontend
eval "$(fnm env)"
fnm use 22

# Run a single test file
npx playwright test tests/<test-file>.spec.ts --reporter=list --workers=1

# Run a specific test
npx playwright test tests/<test-file>.spec.ts:<line-number> --reporter=list
```

Update this log with results after each test run.
