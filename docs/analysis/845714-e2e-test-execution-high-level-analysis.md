# High-Level Analysis: E2E Test Execution and Issue Identification

**Analysis Code:** 845714
**Date:** 2025-11-29
**Type:** PLA_1 High-Level Analysis
**Status:** Awaiting Feedback

## User Story

As a **QA Engineer/Developer**, I need to **run all pending E2E tests and identify issues** so that I can **ensure the frontend application works correctly and fix any broken functionality before deployment**.

## Business Problem

The frontend E2E test suite has 6 pending test files that have not been executed or verified. These tests cover critical user flows including:
- Password reset functionality
- User settings management
- Forecast CRUD operations
- Project performance dashboard
- Cost element tab navigation
- Time machine feature

Without running these tests, we cannot verify that these features work correctly, which could lead to production bugs and user frustration.

## Technical Approach Overview

The approach involves:
1. **Systematic Test Execution**: Run each pending test file individually to isolate issues
2. **Issue Identification**: Capture test failures, timeouts, and errors
3. **Root Cause Analysis**: Analyze failures to determine underlying causes
4. **Documentation**: Document findings and recommended fixes
5. **Fix Implementation**: Apply fixes and re-run tests to verify

## CODEBASE PATTERN ANALYSIS

### Existing Test Patterns

#### 1. Test File Structure Pattern
**Location:** `frontend/tests/*.spec.ts`

**Pattern:**
- Tests use Playwright with TypeScript
- Setup via `beforeAll` hooks for data seeding
- Use of shared utilities (`utils/user.ts`, `utils/mailcatcher.ts`, `utils/random.ts`)
- API authentication via `ensureApiAuth()` pattern
- Test data seeding using OpenAPI client

**Example:**
```typescript
test.beforeAll(async () => {
  await seedForecastData()
})

test("should create a forecast", async ({ page }) => {
  // Test implementation
})
```

#### 2. API Integration Pattern
**Location:** `frontend/tests/forecast-crud.spec.ts`, `frontend/tests/project-performance-dashboard.spec.ts`

**Pattern:**
- Direct API calls using generated OpenAPI client
- Authentication via `LoginService.loginAccessToken()`
- Token storage in `OpenAPI.TOKEN`
- Error handling via `callApi` wrapper function

**Example:**
```typescript
async function ensureApiAuth() {
  if (OpenAPI.TOKEN) return
  OpenAPI.BASE = process.env.VITE_API_URL
  const token = await LoginService.loginAccessToken({...})
  OpenAPI.TOKEN = token.access_token
}
```

#### 3. Test Data Seeding Pattern
**Location:** Multiple test files use `beforeAll` for seeding

**Pattern:**
- Create project → Create WBE → Create Cost Element → Create related entities
- Store IDs in shared object for test use
- Use timestamps for unique identifiers

**Example:**
```typescript
const seededData: { projectId?: string; wbeId?: string } = {}

test.beforeAll(async () => {
  const project = await ProjectsService.createProject({...})
  seededData.projectId = project.project_id
})
```

### Architectural Layers

1. **Test Layer**: Playwright E2E tests (`frontend/tests/`)
2. **UI Layer**: React components with Chakra UI (`frontend/src/components/`)
3. **API Layer**: Generated OpenAPI client (`frontend/src/client/`)
4. **Backend Layer**: FastAPI with PostgreSQL (`backend/app/`)

## INTEGRATION TOUCHPOINT MAPPING

### Methods/Modules Requiring Modification

#### 1. Test Files (Primary Focus)
- `frontend/tests/forecast-crud.spec.ts`
  - **Issue**: Selector specificity for "Forecasts" tab
  - **Fix**: Update selectors to use role-based approach
  - **Lines**: 131, 134, 160

- `frontend/tests/reset-password.spec.ts`
  - **Issue**: Email polling hanging
  - **Fix**: Improve `findLastEmail` error handling and timeout logic
  - **Lines**: 47-51, 102-106

- `frontend/tests/user-settings.spec.ts`
  - **Issue**: Test execution hanging (needs investigation)
  - **Fix**: TBD after investigation

#### 2. Test Utilities
- `frontend/tests/utils/mailcatcher.ts`
  - **Issue**: Email polling may hang indefinitely
  - **Fix**: Add better error handling, logging, and timeout management
  - **Lines**: 33-62

#### 3. Test Configuration
- `frontend/playwright.config.ts`
  - **Potential**: May need timeout adjustments
  - **Current**: Uses default timeouts

### System Dependencies

1. **Docker Services**:
   - `pesta-backend-1`: FastAPI backend (port 8010)
   - `pesta-db-1`: PostgreSQL database
   - `pesta-mailcatcher-1`: Email testing service (port 1080)

2. **Environment Variables**:
   - `VITE_API_URL`: Backend API URL
   - `MAILCATCHER_HOST`: Mailcatcher service URL
   - `FIRST_SUPERUSER`: Test user email
   - `FIRST_SUPERUSER_PASSWORD`: Test user password

3. **External Services**:
   - Mailcatcher API: `http://localhost:1080/messages`
   - Backend API: `http://localhost:8010/api/v1/`

### Configuration Patterns

**Location:** `frontend/tests/config.ts`
- Loads environment variables from `../../.env`
- Validates required variables
- Exports constants for test use

**Pattern:**
```typescript
dotenv.config({ path: path.join(__dirname, "../../.env") })
const { FIRST_SUPERUSER, FIRST_SUPERUSER_PASSWORD } = process.env
if (typeof FIRST_SUPERUSER !== "string") {
  throw new Error("Environment variable FIRST_SUPERUSER is undefined")
}
```

## ABSTRACTION INVENTORY

### Existing Abstractions to Leverage

#### 1. API Call Wrapper
**Location:** Multiple test files
```typescript
async function callApi<T>(label: string, fn: () => Promise<T>): Promise<T> {
  try {
    return await fn()
  } catch (error) {
    console.error(`API error during ${label}:`, error)
    throw error
  }
}
```
**Usage**: Wrap all API calls for consistent error handling

#### 2. Authentication Helper
**Location:** `frontend/tests/forecast-crud.spec.ts`, `frontend/tests/project-performance-dashboard.spec.ts`
```typescript
async function ensureApiAuth() {
  if (OpenAPI.TOKEN) return
  // ... authentication logic
}
```
**Usage**: Ensure API is authenticated before making calls

#### 3. User Utilities
**Location:** `frontend/tests/utils/user.ts`
- `logInUser(page, email, password)`
- `logOutUser(page)`
- `signUpNewUser(page, fullName, email, password)`

#### 4. Random Data Generators
**Location:** `frontend/tests/utils/random.ts`
- `randomEmail()`
- `randomPassword()`

#### 5. Email Utilities
**Location:** `frontend/tests/utils/mailcatcher.ts`
- `findLastEmail({ request, filter, timeout })`
- **Issue**: Needs improvement for reliability

### Test Utilities Available

- **Auth Setup**: `frontend/tests/auth.setup.ts` - Handles authentication
- **Private API**: `frontend/tests/utils/privateApi.ts` - Direct API access
- **Config**: `frontend/tests/config.ts` - Environment configuration

### Patterns for Dependency Injection

- **Service Location**: OpenAPI client uses static methods
- **Context Providers**: React context for branch and time machine
- **Query Management**: TanStack Query for data fetching

## ALTERNATIVE APPROACHES

### Approach 1: Fix Tests Incrementally (Recommended)

**Description:**
- Fix one test file at a time
- Run test after each fix to verify
- Document fixes as we go

**Pros:**
- Low risk - changes are isolated
- Easy to verify fixes work
- Follows TDD principles
- Can stop at any point with partial progress

**Cons:**
- May take longer overall
- Requires multiple test runs

**Alignment with Architecture:**
- ✅ Follows existing test patterns
- ✅ Respects incremental change principle
- ✅ Maintains test isolation

**Complexity:** Low
**Risk:** Low

### Approach 2: Refactor Test Infrastructure First

**Description:**
- Improve test utilities (mailcatcher, selectors) first
- Then run all tests
- Fix remaining issues

**Pros:**
- Addresses root causes
- May fix multiple tests at once
- Improves test infrastructure

**Cons:**
- Higher risk - larger changes
- May introduce new issues
- Harder to verify what fixed what

**Alignment with Architecture:**
- ⚠️ Larger scope than needed
- ⚠️ May violate incremental change principle

**Complexity:** Medium
**Risk:** Medium

### Approach 3: Mock External Dependencies

**Description:**
- Mock mailcatcher API responses
- Mock slow API calls
- Focus on UI interactions

**Pros:**
- Faster test execution
- More reliable (no external dependencies)
- Better for CI/CD

**Cons:**
- Doesn't test real integrations
- Requires significant refactoring
- May miss integration issues

**Alignment with Architecture:**
- ⚠️ Changes test philosophy (E2E vs integration)
- ⚠️ Requires new mocking infrastructure

**Complexity:** High
**Risk:** Medium

## ARCHITECTURAL IMPACT ASSESSMENT

### Principles Followed

1. **Test Isolation**: Each test file is independent
2. **Data Seeding**: Tests create their own data
3. **API Integration**: Tests use real API (not mocks)
4. **Error Handling**: Consistent error handling patterns

### Principles Potentially Violated

1. **Test Reliability**: Some tests are flaky (timing issues)
2. **Test Speed**: Email tests are slow (polling)
3. **Error Visibility**: Some failures are hard to debug

### Future Maintenance Burden

**Low Risk:**
- Test fixes are isolated to test files
- No production code changes required
- Changes are well-documented

**Medium Risk:**
- Test utilities may need ongoing maintenance
- Selector updates needed if UI changes
- Email testing infrastructure needs monitoring

**High Risk:**
- None identified

### Testing Challenges

1. **Timing Issues**: Race conditions between UI and API
2. **External Dependencies**: Mailcatcher availability
3. **Selector Stability**: UI changes break selectors
4. **Test Data Management**: Cleanup and isolation
5. **Debugging**: Hard to debug hanging tests

## Ambiguities and Missing Information

1. **Backend Service Status**: Need to verify backend is running and responsive
2. **Email Configuration**: Need to verify backend email settings point to mailcatcher
3. **Test Execution Environment**: Need to verify all environment variables are set
4. **User Settings Test**: Need to investigate why it's hanging
5. **Remaining Tests**: Need to run and analyze the 3 untested files

## Risks and Unknown Factors

1. **Test Flakiness**: Some tests may be inherently flaky
2. **Environment Differences**: Tests may behave differently in CI vs local
3. **Data Conflicts**: Tests may interfere with each other if not properly isolated
4. **Service Availability**: External services (mailcatcher) may be unavailable
5. **Performance**: Slow tests may timeout in CI environment

## Recommendations

1. **Immediate Actions**:
   - Fix forecast-crud.spec.ts selector issue
   - Improve mailcatcher email polling reliability
   - Investigate user-settings.spec.ts hanging issue

2. **Short-term Actions**:
   - Run remaining 3 test files
   - Document all findings
   - Apply fixes and verify

3. **Long-term Improvements**:
   - Add test IDs to UI components for stable selectors
   - Improve test utilities for better error handling
   - Consider test parallelization for faster execution
   - Add test retry logic for flaky tests

## Next Steps

1. ✅ **Completed**: Created analysis documents
2. ⏳ **Pending**: Wait for user feedback on analysis
3. ⏳ **Pending**: Implement fixes based on feedback
4. ⏳ **Pending**: Run all tests and verify fixes
5. ⏳ **Pending**: Update test log with results

---

**Awaiting feedback before proceeding to detailed planning and implementation.**
