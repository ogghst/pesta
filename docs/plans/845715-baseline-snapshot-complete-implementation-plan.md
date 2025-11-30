# Implementation Plan: Complete Baseline Snapshot

**Plan ID:** 845715
**Based on Specification:** `docs/plans/845715-baseline-snapshot-complete-specification.md`
**Date:** 2025-11-29

## EXECUTION CONTEXT

- **TDD Discipline**: All steps follow red-green-refactor cycle
- **Human Supervision**: Pause at checkpoints for review
- **Stop/Go Criteria**: Each step has explicit acceptance criteria
- **Maximum Iterations**: 3 attempts per step before seeking help

## IMPLEMENTATION STEPS

### Phase 1: Database Models and Schemas

#### Step 1.1: Create BaselineWBE Model [UNIT]

**Description**: Create the `BaselineWBE` model following the `BaselineCostElement` pattern.

**Test-First Requirement**:
- Create test: `test_baseline_wbe_model_creation()` in `backend/tests/models/test_baseline_wbe.py`
- Test must fail (model doesn't exist)

**Implementation**:
1. Create `backend/app/models/baseline_wbe.py`
2. Define `BaselineWBEBase` with all EVM metric fields
3. Define `BaselineWBECreate`, `BaselineWBEUpdate`, `BaselineWBE`, `BaselineWBEPublic`
4. Add foreign keys to `BaselineLog` and `WBE`
5. Use `VersionStatusMixin`

**Acceptance Criteria**:
- ✅ Model file exists and follows `BaselineCostElement` pattern exactly
- ✅ All EVM metric fields defined (PV, EV, AC, BAC, EAC, CPI, SPI, TCPI, CV, SV, forecasted_quality)
- ✅ Foreign keys defined correctly
- ✅ Test passes: can create and persist BaselineWBE
- ✅ Type hints are correct
- ✅ No linting errors

**Expected Files**:
- `backend/app/models/baseline_wbe.py` (NEW)
- `backend/tests/models/test_baseline_wbe.py` (NEW)

**Dependencies**: None

---

#### Step 1.2: Create BaselineProject Model [UNIT]

**Description**: Create the `BaselineProject` model following the `BaselineCostElement` pattern.

**Test-First Requirement**:
- Create test: `test_baseline_project_model_creation()` in `backend/tests/models/test_baseline_project.py`
- Test must fail (model doesn't exist)

**Implementation**:
1. Create `backend/app/models/baseline_project.py`
2. Define `BaselineProjectBase` with all EVM metric fields
3. Define `BaselineProjectCreate`, `BaselineProjectUpdate`, `BaselineProject`, `BaselineProjectPublic`
4. Add foreign keys to `BaselineLog` and `Project`
5. Use `VersionStatusMixin`

**Acceptance Criteria**:
- ✅ Model file exists and follows `BaselineCostElement` pattern exactly
- ✅ All EVM metric fields defined (PV, EV, AC, BAC, EAC, CPI, SPI, TCPI, CV, SV, forecasted_quality)
- ✅ Foreign keys defined correctly
- ✅ Test passes: can create and persist BaselineProject
- ✅ Type hints are correct
- ✅ No linting errors

**Expected Files**:
- `backend/app/models/baseline_project.py` (NEW)
- `backend/tests/models/test_baseline_project.py` (NEW)

**Dependencies**: None

---

#### Step 1.3: Export New Models [UNIT]

**Description**: Add exports for new models to `__init__.py`.

**Test-First Requirement**:
- Create test: `test_models_import()` - verify imports work
- Test must fail (imports don't exist)

**Implementation**:
1. Open `backend/app/models/__init__.py`
2. Add imports for all BaselineWBE classes
3. Add imports for all BaselineProject classes
4. Add to `__all__` list if it exists

**Acceptance Criteria**:
- ✅ All BaselineWBE classes can be imported
- ✅ All BaselineProject classes can be imported
- ✅ Test passes: imports work without errors
- ✅ Follows existing export pattern

**Expected Files**:
- `backend/app/models/__init__.py` (MODIFY)

**Dependencies**: Steps 1.1, 1.2

---

### Phase 2: Database Migration

#### Step 2.1: Create Database Migration [INTEGRATION]

**Description**: Create Alembic migration for new tables.

**Test-First Requirement**:
- Migration script must be created
- Test: Run migration up, verify tables exist
- Test: Run migration down, verify tables removed

**Implementation**:
1. Run `alembic revision --autogenerate -m "create_baseline_wbe_and_project"`
2. Review generated migration
3. Add indexes on `baseline_id`, `wbe_id`, `project_id`
4. Verify foreign key constraints
5. Test migration up and down

**Acceptance Criteria**:
- ✅ Migration file created
- ✅ `baseline_wbe` table created with all columns
- ✅ `baseline_project` table created with all columns
- ✅ Foreign key constraints added
- ✅ Indexes added on key columns
- ✅ Migration is reversible (down migration works)
- ✅ No migration errors

**Expected Files**:
- `backend/alembic/versions/XXXX_create_baseline_wbe_and_project.py` (NEW)

**Dependencies**: Steps 1.1, 1.2, 1.3

**Checkpoint**: After this step, pause and verify database schema is correct.

---

### Phase 3: Baseline Creation Logic

#### Step 3.1: Create Helper Function for WBE Snapshot [UNIT]

**Description**: Create function to calculate and create BaselineWBE records.

**Test-First Requirement**:
- Create test: `test_create_baseline_wbe_snapshot()` in `backend/tests/api/routes/test_baseline_logs.py`
- Test must fail (function doesn't exist)

**Implementation**:
1. Create `_create_baseline_wbe_snapshot()` helper function in `baseline_logs.py`
2. Function signature: `(session, baseline_log, wbe, control_date) -> BaselineWBE`
3. Get all cost elements for WBE (respecting control_date)
4. Calculate metrics for each cost element using `get_cost_element_evm_metrics()`
5. Aggregate using `aggregate_cost_element_metrics()`
6. Create BaselineWBE record with aggregated metrics
7. Handle empty WBE (zero metrics)

**Acceptance Criteria**:
- ✅ Function exists and follows existing patterns
- ✅ Calculates metrics correctly using existing services
- ✅ Creates BaselineWBE record with all metrics
- ✅ Handles empty WBE (returns zero metrics)
- ✅ Respects control_date (time machine)
- ✅ Test passes: can create WBE snapshot
- ✅ Metrics match sum of cost element metrics

**Expected Files**:
- `backend/app/api/routes/baseline_logs.py` (MODIFY)
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: Steps 1.1, 1.2, 1.3, 2.1

---

#### Step 3.2: Create Helper Function for Project Snapshot [UNIT]

**Description**: Create function to calculate and create BaselineProject record.

**Test-First Requirement**:
- Create test: `test_create_baseline_project_snapshot()` in `backend/tests/api/routes/test_baseline_logs.py`
- Test must fail (function doesn't exist)

**Implementation**:
1. Create `_create_baseline_project_snapshot()` helper function in `baseline_logs.py`
2. Function signature: `(session, baseline_log, project, control_date) -> BaselineProject`
3. Get all WBEs for project (respecting control_date)
4. For each WBE, get BaselineWBE metrics (or calculate if not yet created)
5. Aggregate WBE metrics using `aggregate_cost_element_metrics()`
6. Create BaselineProject record with aggregated metrics
7. Handle empty project (zero metrics)

**Acceptance Criteria**:
- ✅ Function exists and follows existing patterns
- ✅ Calculates metrics correctly by aggregating WBE metrics
- ✅ Creates BaselineProject record with all metrics
- ✅ Handles empty project (returns zero metrics)
- ✅ Respects control_date (time machine)
- ✅ Test passes: can create project snapshot
- ✅ Metrics match sum of WBE metrics

**Expected Files**:
- `backend/app/api/routes/baseline_logs.py` (MODIFY)
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: Steps 1.1, 1.2, 1.3, 2.1, 3.1

---

#### Step 3.3: Integrate Snapshot Creation into Baseline Flow [INTEGRATION]

**Description**: Modify baseline creation to create all snapshots (cost element, WBE, project).

**Test-First Requirement**:
- Modify test: `test_create_baseline_creates_all_snapshots()` in `backend/tests/api/routes/test_baseline_logs.py`
- Test must fail (snapshots not created)

**Implementation**:
1. Modify `create_baseline_cost_elements_for_baseline_log()` function
2. After creating cost element snapshots, create WBE snapshots
3. After creating WBE snapshots, create project snapshot
4. Wrap all in transaction (existing transaction)
5. Handle errors (rollback on failure)

**Acceptance Criteria**:
- ✅ Baseline creation creates cost element snapshots (existing)
- ✅ Baseline creation creates WBE snapshots for all WBEs
- ✅ Baseline creation creates project snapshot
- ✅ All within same transaction
- ✅ Errors cause rollback (no partial snapshots)
- ✅ Test passes: complete baseline creation works
- ✅ Metrics are correct at all levels

**Expected Files**:
- `backend/app/api/routes/baseline_logs.py` (MODIFY)
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: Steps 3.1, 3.2

**Checkpoint**: After this step, pause and verify baseline creation works end-to-end.

---

### Phase 4: API Endpoints

#### Step 4.1: Add WBE Snapshots List Endpoint [INTEGRATION]

**Description**: Create GET endpoint to list all WBE snapshots for a baseline.

**Test-First Requirement**:
- Create test: `test_get_baseline_wbe_snapshots()` in `backend/tests/api/routes/test_baseline_logs.py`
- Test must fail (endpoint doesn't exist)

**Implementation**:
1. Add route: `GET /projects/{project_id}/baseline-logs/{baseline_id}/wbe-snapshots`
2. Validate project_id and baseline_id
3. Query BaselineWBE records for baseline_id
4. Apply status filters
5. Return list of BaselineWBEPublic
6. Handle 404 if baseline not found or wrong project

**Acceptance Criteria**:
- ✅ Endpoint exists and is accessible
- ✅ Returns list of BaselineWBEPublic
- ✅ Validates project_id and baseline_id
- ✅ Applies status filters
- ✅ Returns 404 for invalid requests
- ✅ Test passes: endpoint works correctly

**Expected Files**:
- `backend/app/api/routes/baseline_logs.py` (MODIFY)
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: Steps 1.1, 1.2, 1.3, 2.1, 3.3

---

#### Step 4.2: Add WBE Snapshot Detail Endpoint [INTEGRATION]

**Description**: Create GET endpoint to retrieve specific WBE snapshot.

**Test-First Requirement**:
- Create test: `test_get_baseline_wbe_snapshot_detail()` in `backend/tests/api/routes/test_baseline_logs.py`
- Test must fail (endpoint doesn't exist)

**Implementation**:
1. Add route: `GET /projects/{project_id}/baseline-logs/{baseline_id}/wbe-snapshots/{wbe_id}`
2. Validate project_id, baseline_id, and wbe_id
3. Query BaselineWBE record
4. Apply status filters
5. Return BaselineWBEPublic
6. Handle 404 if not found

**Acceptance Criteria**:
- ✅ Endpoint exists and is accessible
- ✅ Returns BaselineWBEPublic
- ✅ Validates all IDs
- ✅ Returns 404 for invalid requests
- ✅ Test passes: endpoint works correctly

**Expected Files**:
- `backend/app/api/routes/baseline_logs.py` (MODIFY)
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: Steps 1.1, 1.2, 1.3, 2.1, 3.3

---

#### Step 4.3: Add Project Snapshot Endpoint [INTEGRATION]

**Description**: Create GET endpoint to retrieve project snapshot.

**Test-First Requirement**:
- Create test: `test_get_baseline_project_snapshot()` in `backend/tests/api/routes/test_baseline_logs.py`
- Test must fail (endpoint doesn't exist)

**Implementation**:
1. Add route: `GET /projects/{project_id}/baseline-logs/{baseline_id}/project-snapshot`
2. Validate project_id and baseline_id
3. Query BaselineProject record
4. Apply status filters
5. Return BaselineProjectPublic
6. Handle 404 if not found

**Acceptance Criteria**:
- ✅ Endpoint exists and is accessible
- ✅ Returns BaselineProjectPublic
- ✅ Validates project_id and baseline_id
- ✅ Returns 404 for invalid requests
- ✅ Test passes: endpoint works correctly

**Expected Files**:
- `backend/app/api/routes/baseline_logs.py` (MODIFY)
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: Steps 1.1, 1.2, 1.3, 2.1, 3.3

**Checkpoint**: After this step, pause and verify all API endpoints work.

---

### Phase 5: Testing and Validation

#### Step 5.1: Integration Tests for Baseline Creation [INTEGRATION]

**Description**: Comprehensive tests for baseline creation with all snapshots.

**Test-First Requirement**:
- Create comprehensive test suite
- Tests should verify all aspects of baseline creation

**Implementation**:
1. Test baseline creation with multiple WBEs and cost elements
2. Verify metrics match calculated values
3. Verify WBE metrics = sum of cost element metrics
4. Verify project metrics = sum of WBE metrics
5. Test edge cases (empty project, empty WBE, no data)
6. Test time machine (baseline_date as control date)

**Acceptance Criteria**:
- ✅ Test suite covers all scenarios
- ✅ All tests pass
- ✅ Metrics verified to be correct
- ✅ Aggregation verified to be correct
- ✅ Edge cases handled

**Expected Files**:
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: All previous steps

---

#### Step 5.2: Integration Tests for API Endpoints [INTEGRATION]

**Description**: Tests for new API endpoints.

**Test-First Requirement**:
- Create test suite for all new endpoints
- Tests should cover success and error cases

**Implementation**:
1. Test all new endpoints with valid data
2. Test error cases (404, wrong project, etc.)
3. Test status filtering
4. Test empty results
5. Test authentication/authorization

**Acceptance Criteria**:
- ✅ All endpoints tested
- ✅ Success cases work
- ✅ Error cases handled correctly
- ✅ All tests pass

**Expected Files**:
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: Steps 4.1, 4.2, 4.3

---

#### Step 5.3: End-to-End Test [E2E]

**Description**: Full workflow test from baseline creation to retrieval.

**Test-First Requirement**:
- Create E2E test
- Test complete workflow

**Implementation**:
1. Create baseline with complete project hierarchy
2. Verify all snapshots created correctly
3. Retrieve snapshots at all levels
4. Verify metrics are correct
5. Compare to operational calculations

**Acceptance Criteria**:
- ✅ E2E test passes
- ✅ Complete workflow works
- ✅ Metrics verified end-to-end
- ✅ No regressions

**Expected Files**:
- `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)

**Dependencies**: All previous steps

**Final Checkpoint**: After this step, verify complete implementation works.

---

## TDD DISCIPLINE RULES

1. **Red Phase**: Write failing test first
2. **Green Phase**: Write minimal code to make test pass
3. **Refactor Phase**: Improve code while keeping tests green
4. **Maximum Iterations**: 3 attempts per step before asking for help
5. **Test Coverage**: All new code must have tests
6. **No Production Code Without Tests**: Every production change must have corresponding test

## PROCESS CHECKPOINTS

**Checkpoint 1**: After Step 2.1 (Database Migration)
- Question: "Should we continue with the plan as-is?"
- Question: "Does the database schema match our expectations?"
- Action: Review migration, verify tables created correctly

**Checkpoint 2**: After Step 3.3 (Baseline Creation Integration)
- Question: "Does baseline creation work end-to-end?"
- Question: "Are metrics calculated correctly at all levels?"
- Action: Test baseline creation manually, verify metrics

**Checkpoint 3**: After Step 4.3 (All API Endpoints)
- Question: "Do all API endpoints work correctly?"
- Question: "Are there any breaking changes?"
- Action: Test all endpoints, verify backward compatibility

**Final Checkpoint**: After Step 5.3 (E2E Test)
- Question: "Is the implementation complete?"
- Question: "Are there any remaining issues?"
- Action: Review complete implementation, verify all requirements met

## SCOPE BOUNDARIES

**In Scope**:
- Creating BaselineWBE and BaselineProject models
- Creating database migration
- Modifying baseline creation to create all snapshots
- Adding API endpoints for retrieving snapshots
- Comprehensive testing

**Out of Scope** (Do Not Implement):
- Backfilling existing baselines (future work)
- Baseline comparison UI (frontend work)
- Performance optimization beyond basic indexes (future work)
- Baseline update functionality (snapshots are immutable)

**If Useful Improvements Found**:
- Ask user for confirmation before implementing
- Document in separate enhancement request

## ROLLBACK STRATEGY

**Safe Rollback Points**:

1. **After Step 2.1**: Rollback migration
   - Run: `alembic downgrade -1`
   - Removes new tables
   - No data loss (tables are new)

2. **After Step 3.3**: Disable snapshot creation
   - Comment out WBE/Project snapshot creation code
   - Baseline creation still works (cost element snapshots)
   - No breaking changes

3. **After Step 4.3**: Remove new endpoints
   - Comment out new endpoint routes
   - Existing functionality unchanged
   - No breaking changes

**Alternative Approach if Current Fails**:
- If three-level snapshot approach fails, consider:
  - Approach 2: Single BaselineMetrics table (from analysis)
  - Approach 3: Store only in BaselineLog (from analysis)
- Must get user approval before switching approaches

## IMPLEMENTATION NOTES

### Code Quality Standards
- Follow existing code style
- Use type hints
- Add docstrings
- Follow naming conventions
- No linting errors

### Testing Standards
- Unit tests for models and helper functions
- Integration tests for API endpoints
- E2E test for complete workflow
- Edge case coverage
- Performance considerations

### Documentation
- Update API documentation (OpenAPI/Swagger)
- Code comments for complex logic
- Update data model documentation if needed

## ESTIMATED TIMELINE

- **Phase 1**: ~50 minutes (Models and Schemas)
- **Phase 2**: ~25 minutes (Database Migration)
- **Phase 3**: ~90 minutes (Baseline Creation Logic)
- **Phase 4**: ~60 minutes (API Endpoints)
- **Phase 5**: ~105 minutes (Testing and Validation)

**Total Estimated Time**: ~5.5 hours

*Note: Times are estimates and may vary based on complexity and debugging needs.*
