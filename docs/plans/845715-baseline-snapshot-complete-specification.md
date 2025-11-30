# Detailed Specification: Complete Baseline Snapshot Implementation

**Specification ID:** 845715
**Based on Analysis:** `docs/analysis/845715-baseline-snapshot-complete-analysis.md`
**Date:** 2025-11-29

## 1. FEATURE SPECIFICATION

### 1.1 User-Facing Description

**What users will be able to do:**

1. **Create Complete Baselines**: When creating a baseline, the system will automatically:
   - Capture cost element snapshots (existing functionality)
   - Calculate and store WBE-level EVM metrics as snapshot records
   - Calculate and store project-level EVM metrics as a snapshot record
   - Store all EVM metrics (PV, EV, AC, BAC, EAC, CPI, SPI, TCPI, CV, SV) at each level

2. **Retrieve Baseline Snapshots**: Users can retrieve baseline snapshots at any level:
   - Project-level baseline snapshot with all aggregated metrics
   - WBE-level baseline snapshots for each WBE in the project
   - Cost element-level baseline snapshots (existing functionality)

3. **Compare Baselines**: Users can compare baselines at any level:
   - Compare project metrics between two baselines
   - Compare WBE metrics between two baselines
   - Compare cost element metrics between two baselines

4. **Historical Analysis**: Users can analyze project performance over time:
   - View how metrics changed between baseline milestones
   - Track performance trends at project, WBE, and cost element levels
   - Identify variance patterns across baseline periods

### 1.2 Success Criteria

**Functional Success:**
- ✅ Baseline creation creates `BaselineWBE` records for all WBEs in the project
- ✅ Baseline creation creates one `BaselineProject` record for the project
- ✅ All EVM metrics (PV, EV, AC, BAC, EAC, CPI, SPI, TCPI, CV, SV) are calculated and stored at each level
- ✅ WBE metrics match the sum of cost element metrics for that WBE
- ✅ Project metrics match the sum of WBE metrics for that project
- ✅ Metrics are calculated using `baseline_date` as the control date
- ✅ Only operational data on or before `baseline_date` is included in calculations
- ✅ Baseline snapshots are immutable (versioned but not updated after creation)

**Performance Success:**
- ✅ Baseline creation completes within 5 seconds for projects with up to 20 WBEs and 300 cost elements
- ✅ Baseline snapshot retrieval completes within 1 second
- ✅ Database queries use appropriate indexes

**Data Integrity Success:**
- ✅ All foreign key constraints are enforced
- ✅ Baseline snapshots cannot be created without valid `BaselineLog`
- ✅ Baseline snapshots reference correct WBE/Project entities
- ✅ Metrics stored match calculated values from operational data

**API Success:**
- ✅ New endpoints return baseline snapshots at WBE and Project levels
- ✅ Existing endpoints continue to work without breaking changes
- ✅ Response schemas include all EVM metrics
- ✅ Error handling provides clear messages for invalid requests

### 1.3 Edge Cases

1. **Empty Project**: Project with no WBEs
   - Should create `BaselineProject` with zero metrics
   - Should not create any `BaselineWBE` records
   - Should not fail or error

2. **Empty WBE**: WBE with no cost elements
   - Should create `BaselineWBE` with zero metrics
   - Should aggregate correctly to project level

3. **No Operational Data**: Cost elements with no costs, earned value, or forecasts
   - Should create snapshots with `actual_ac=None`, `earned_ev=None`, `forecast_eac=None`
   - Should calculate metrics with zero values where appropriate
   - Should handle `None` values in aggregation (treat as zero for sums)

4. **Future Baseline Date**: Baseline created with future date
   - Should use baseline_date as control date
   - Should only include operational data on or before that date
   - Should calculate metrics as if viewing from that future date

5. **Multiple Baselines**: Multiple baselines for same project
   - Each baseline should have independent snapshot records
   - Snapshots should be queryable by `baseline_id`
   - No interference between different baseline snapshots

6. **Cancelled Baseline**: Baseline marked as cancelled
   - Snapshots should still exist and be queryable
   - Status filters should exclude cancelled baselines by default
   - Historical analysis should still work

7. **Large Projects**: Projects with many WBEs and cost elements
   - Should complete within performance targets
   - Should use batch operations where possible
   - Should not cause memory issues

### 1.4 Error Conditions

1. **Invalid Baseline ID**: Requesting snapshot for non-existent baseline
   - **Response**: 404 Not Found
   - **Message**: "Baseline log not found"

2. **Baseline from Different Project**: Requesting snapshot using wrong project_id
   - **Response**: 404 Not Found
   - **Message**: "Baseline log not found" (security: don't reveal existence)

3. **Missing Baseline Log**: Creating snapshot without BaselineLog
   - **Response**: Database constraint violation
   - **Prevention**: Validate BaselineLog exists before creating snapshots

4. **Invalid WBE/Project Reference**: Snapshot references non-existent WBE/Project
   - **Response**: Database constraint violation
   - **Prevention**: Validate references exist before creating snapshots

5. **Calculation Errors**: Metrics calculation fails (division by zero, etc.)
   - **Response**: 500 Internal Server Error
   - **Logging**: Log error details for debugging
   - **Handling**: Use safe calculation functions that handle edge cases

6. **Database Transaction Failure**: Partial snapshot creation fails
   - **Response**: Rollback transaction, return error
   - **Behavior**: No partial snapshots should be created

## 2. TECHNICAL SPECIFICATION

### 2.1 Interfaces to Create or Modify

#### 2.1.1 New Database Models

**`BaselineWBE` Model** (`backend/app/models/baseline_wbe.py`)
```python
class BaselineWBEBase(SQLModel):
    """Base baseline WBE schema with EVM metrics."""
    planned_value: Decimal
    earned_value: Decimal
    actual_cost: Decimal
    budget_bac: Decimal
    eac: Decimal
    forecasted_quality: Decimal
    cpi: Decimal | None
    spi: Decimal | None
    tcpi: Decimal | Literal["overrun"] | None
    cost_variance: Decimal
    schedule_variance: Decimal

class BaselineWBE(BaselineWBEBase, VersionStatusMixin, table=True):
    baseline_wbe_id: uuid.UUID (PK)
    baseline_id: uuid.UUID (FK → BaselineLog)
    wbe_id: uuid.UUID (FK → WBE)
    created_at: datetime
```

**`BaselineProject` Model** (`backend/app/models/baseline_project.py`)
```python
class BaselineProjectBase(SQLModel):
    """Base baseline project schema with EVM metrics."""
    planned_value: Decimal
    earned_value: Decimal
    actual_cost: Decimal
    budget_bac: Decimal
    eac: Decimal
    forecasted_quality: Decimal
    cpi: Decimal | None
    spi: Decimal | None
    tcpi: Decimal | Literal["overrun"] | None
    cost_variance: Decimal
    schedule_variance: Decimal

class BaselineProject(BaselineProjectBase, VersionStatusMixin, table=True):
    baseline_project_id: uuid.UUID (PK)
    baseline_id: uuid.UUID (FK → BaselineLog)
    project_id: uuid.UUID (FK → Project)
    created_at: datetime
```

#### 2.1.2 Modified Functions

**`create_baseline_cost_elements_for_baseline_log()`** (`backend/app/api/routes/baseline_logs.py`)
- **Current**: Creates only `BaselineCostElement` records
- **Modified**: Also creates `BaselineWBE` and `BaselineProject` records
- **New Logic**:
  1. Create cost element snapshots (existing)
  2. Group cost elements by WBE
  3. For each WBE, calculate aggregated metrics and create `BaselineWBE`
  4. Calculate project-level aggregated metrics and create `BaselineProject`

#### 2.1.3 New API Endpoints

**GET `/projects/{project_id}/baseline-logs/{baseline_id}/wbe-snapshots`**
- Returns: `list[BaselineWBEPublic]`
- Lists all WBE snapshots for a baseline

**GET `/projects/{project_id}/baseline-logs/{baseline_id}/wbe-snapshots/{wbe_id}`**
- Returns: `BaselineWBEPublic`
- Returns specific WBE snapshot for a baseline

**GET `/projects/{project_id}/baseline-logs/{baseline_id}/project-snapshot`**
- Returns: `BaselineProjectPublic`
- Returns project snapshot for a baseline

### 2.2 Data Structures Required

**BaselineWBE Schema Classes:**
- `BaselineWBEBase`: Base fields (EVM metrics)
- `BaselineWBECreate`: For creation (includes `baseline_id`, `wbe_id`)
- `BaselineWBEUpdate`: For updates (all fields optional, but snapshots are immutable)
- `BaselineWBE`: Database model
- `BaselineWBEPublic`: API response schema

**BaselineProject Schema Classes:**
- `BaselineProjectBase`: Base fields (EVM metrics)
- `BaselineProjectCreate`: For creation (includes `baseline_id`, `project_id`)
- `BaselineProjectUpdate`: For updates (all fields optional, but snapshots are immutable)
- `BaselineProject`: Database model
- `BaselineProjectPublic`: API response schema

**EVM Metrics Structure:**
- Reuse `WBEEVMMetrics` and `ProjectEVMMetrics` dataclasses from `evm_aggregation.py`
- Convert dataclass to model fields when creating snapshot records

### 2.3 Integration Points with Existing Code

1. **EVM Aggregation Service** (`backend/app/services/evm_aggregation.py`)
   - Use `get_cost_element_evm_metrics()` for cost element calculations
   - Use `aggregate_cost_element_metrics()` for WBE and Project aggregation
   - Convert dataclass results to model fields

2. **Time Machine Service** (`backend/app/services/time_machine.py`)
   - Use `apply_time_machine_filters()` when fetching operational data
   - Use `baseline_date` as control date for all calculations

3. **Branch Filtering** (`backend/app/services/branch_filtering.py`)
   - Use `apply_branch_filters()` when fetching operational data
   - Use `apply_status_filters()` to exclude inactive records

4. **Entity Versioning** (`backend/app/services/entity_versioning.py`)
   - Use `create_entity_with_version()` for creating snapshot records
   - Follow same versioning pattern as `BaselineCostElement`

5. **Baseline Logs Route** (`backend/app/api/routes/baseline_logs.py`)
   - Modify `create_baseline_cost_elements_for_baseline_log()` function
   - Add new endpoint handlers for WBE and Project snapshots

6. **Models Init** (`backend/app/models/__init__.py`)
   - Export new models and schemas
   - Follow existing export pattern

### 2.4 Configuration or Settings Needed

- **No new configuration required**
- Uses existing database connection
- Uses existing versioning and status management
- Uses existing time machine control date mechanism

### 2.5 Security Considerations

1. **Authorization**:
   - Reuse existing authentication/authorization middleware
   - Users must have access to project to view baseline snapshots
   - Validate `project_id` matches baseline's project

2. **Data Validation**:
   - Validate `baseline_id` exists and belongs to `project_id`
   - Validate `wbe_id` exists and belongs to `project_id`
   - Prevent creation of snapshots without valid BaselineLog

3. **SQL Injection**:
   - Use SQLModel/SQLAlchemy ORM (parameterized queries)
   - No raw SQL queries

4. **Data Integrity**:
   - Foreign key constraints enforce referential integrity
   - Database transactions ensure atomicity

## 3. TASK BREAKDOWN

### Phase 1: Database Models and Schemas [UNIT]

**Task 1.1: Create BaselineWBE Model** [UNIT]
- **Description**: Create `backend/app/models/baseline_wbe.py` with all schema classes
- **Acceptance Criteria**:
  - Model follows `BaselineCostElement` pattern exactly
  - All EVM metric fields defined with correct types
  - Foreign keys to `BaselineLog` and `WBE`
  - Uses `VersionStatusMixin`
  - All schema classes (Base, Create, Update, Public) defined
- **Test**: `test_baseline_wbe_model_creation()` - Create and persist BaselineWBE
- **Files**: `backend/app/models/baseline_wbe.py` (NEW)
- **Estimated Time**: 20 minutes

**Task 1.2: Create BaselineProject Model** [UNIT]
- **Description**: Create `backend/app/models/baseline_project.py` with all schema classes
- **Acceptance Criteria**:
  - Model follows `BaselineCostElement` pattern exactly
  - All EVM metric fields defined with correct types
  - Foreign keys to `BaselineLog` and `Project`
  - Uses `VersionStatusMixin`
  - All schema classes (Base, Create, Update, Public) defined
- **Test**: `test_baseline_project_model_creation()` - Create and persist BaselineProject
- **Files**: `backend/app/models/baseline_project.py` (NEW)
- **Estimated Time**: 20 minutes

**Task 1.3: Export New Models** [UNIT]
- **Description**: Add exports to `backend/app/models/__init__.py`
- **Acceptance Criteria**:
  - All BaselineWBE classes exported
  - All BaselineProject classes exported
  - Follows existing export pattern
- **Test**: `test_models_import()` - Verify imports work
- **Files**: `backend/app/models/__init__.py` (MODIFY)
- **Estimated Time**: 10 minutes

### Phase 2: Database Migration [INTEGRATION]

**Task 2.1: Create Database Migration** [INTEGRATION]
- **Description**: Create Alembic migration for new tables
- **Acceptance Criteria**:
  - `baseline_wbe` table created with all columns
  - `baseline_project` table created with all columns
  - Foreign key constraints added
  - Indexes on `baseline_id`, `wbe_id`, `project_id`
  - Migration is reversible
- **Test**: Run migration up and down, verify tables exist
- **Files**: `backend/alembic/versions/XXXX_create_baseline_wbe_and_project.py` (NEW)
- **Estimated Time**: 25 minutes

### Phase 3: Baseline Creation Logic [INTEGRATION]

**Task 3.1: Create Helper Function for WBE Snapshot** [UNIT]
- **Description**: Create function to calculate and create BaselineWBE records
- **Acceptance Criteria**:
  - Function takes WBE, baseline_log, and control_date
  - Calculates metrics using `aggregate_cost_element_metrics()`
  - Creates BaselineWBE record with all metrics
  - Handles empty WBE (zero metrics)
- **Test**: `test_create_baseline_wbe_snapshot()` - Verify WBE snapshot creation
- **Files**: `backend/app/api/routes/baseline_logs.py` (MODIFY)
- **Estimated Time**: 30 minutes

**Task 3.2: Create Helper Function for Project Snapshot** [UNIT]
- **Description**: Create function to calculate and create BaselineProject record
- **Acceptance Criteria**:
  - Function takes project, baseline_log, and control_date
  - Calculates metrics by aggregating WBE metrics
  - Creates BaselineProject record with all metrics
  - Handles empty project (zero metrics)
- **Test**: `test_create_baseline_project_snapshot()` - Verify project snapshot creation
- **Files**: `backend/app/api/routes/baseline_logs.py` (MODIFY)
- **Estimated Time**: 30 minutes

**Task 3.3: Integrate Snapshot Creation into Baseline Flow** [INTEGRATION]
- **Description**: Modify `create_baseline_cost_elements_for_baseline_log()` to create all snapshots
- **Acceptance Criteria**:
  - Creates cost element snapshots (existing)
  - Creates WBE snapshots for all WBEs
  - Creates project snapshot
  - All within same transaction
  - Handles errors gracefully (rollback on failure)
- **Test**: `test_create_baseline_creates_all_snapshots()` - Verify complete baseline creation
- **Files**: `backend/app/api/routes/baseline_logs.py` (MODIFY)
- **Estimated Time**: 30 minutes

### Phase 4: API Endpoints [INTEGRATION]

**Task 4.1: Add WBE Snapshots List Endpoint** [INTEGRATION]
- **Description**: GET endpoint to list all WBE snapshots for a baseline
- **Acceptance Criteria**:
  - Returns list of BaselineWBEPublic
  - Validates project_id and baseline_id
  - Applies status filters
  - Returns 404 if baseline not found or wrong project
- **Test**: `test_get_baseline_wbe_snapshots()` - Verify endpoint works
- **Files**: `backend/app/api/routes/baseline_logs.py` (MODIFY)
- **Estimated Time**: 20 minutes

**Task 4.2: Add WBE Snapshot Detail Endpoint** [INTEGRATION]
- **Description**: GET endpoint to retrieve specific WBE snapshot
- **Acceptance Criteria**:
  - Returns BaselineWBEPublic
  - Validates project_id, baseline_id, and wbe_id
  - Returns 404 if not found
- **Test**: `test_get_baseline_wbe_snapshot_detail()` - Verify endpoint works
- **Files**: `backend/app/api/routes/baseline_logs.py` (MODIFY)
- **Estimated Time**: 20 minutes

**Task 4.3: Add Project Snapshot Endpoint** [INTEGRATION]
- **Description**: GET endpoint to retrieve project snapshot
- **Acceptance Criteria**:
  - Returns BaselineProjectPublic
  - Validates project_id and baseline_id
  - Returns 404 if not found
- **Test**: `test_get_baseline_project_snapshot()` - Verify endpoint works
- **Files**: `backend/app/api/routes/baseline_logs.py` (MODIFY)
- **Estimated Time**: 20 minutes

### Phase 5: Testing and Validation [E2E]

**Task 5.1: Integration Tests for Baseline Creation** [INTEGRATION]
- **Description**: Comprehensive tests for baseline creation with all snapshots
- **Acceptance Criteria**:
  - Test baseline creation with multiple WBEs and cost elements
  - Verify metrics match calculated values
  - Verify WBE metrics = sum of cost element metrics
  - Verify project metrics = sum of WBE metrics
  - Test edge cases (empty project, empty WBE, no data)
- **Test**: Multiple test functions in `test_baseline_logs.py`
- **Files**: `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)
- **Estimated Time**: 45 minutes

**Task 5.2: Integration Tests for API Endpoints** [INTEGRATION]
- **Description**: Tests for new API endpoints
- **Acceptance Criteria**:
  - Test all new endpoints with valid data
  - Test error cases (404, wrong project, etc.)
  - Test status filtering
  - Test empty results
- **Test**: New test functions in `test_baseline_logs.py`
- **Files**: `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)
- **Estimated Time**: 30 minutes

**Task 5.3: End-to-End Test** [E2E]
- **Description**: Full workflow test from baseline creation to retrieval
- **Acceptance Criteria**:
  - Create baseline with complete project hierarchy
  - Verify all snapshots created correctly
  - Retrieve snapshots at all levels
  - Verify metrics are correct
- **Test**: `test_baseline_snapshot_e2e()` - Full workflow
- **Files**: `backend/tests/api/routes/test_baseline_logs.py` (MODIFY)
- **Estimated Time**: 30 minutes

## 4. RISK ASSESSMENT

### 4.1 High Risk Areas

1. **Metric Calculation Accuracy** (HIGH)
   - **Risk**: Metrics stored in snapshots don't match operational calculations
   - **Mitigation**:
     - Reuse existing `aggregate_cost_element_metrics()` function
     - Add validation tests comparing snapshot metrics to calculated metrics
     - Test with various data scenarios
   - **Verification**: Compare snapshot metrics to real-time calculations

2. **Data Consistency Across Levels** (MEDIUM)
   - **Risk**: WBE metrics don't equal sum of cost element metrics
   - **Mitigation**:
     - Use same aggregation function for both snapshot and operational data
     - Add validation tests for aggregation consistency
     - Test edge cases (None values, zero values)
   - **Verification**: Assert WBE sum = cost element sum, project sum = WBE sum

3. **Performance with Large Projects** (MEDIUM)
   - **Risk**: Baseline creation takes too long for large projects
   - **Mitigation**:
     - Use batch operations where possible
     - Add database indexes
     - Profile and optimize queries
     - Consider async operations if needed
   - **Verification**: Performance tests with large datasets

4. **Transaction Rollback** (LOW)
   - **Risk**: Partial snapshot creation if error occurs
   - **Mitigation**:
     - Wrap all snapshot creation in database transaction
     - Test rollback scenarios
     - Ensure atomicity
   - **Verification**: Test error scenarios, verify no partial data

### 4.2 Dependencies on External Systems

- **Database**: PostgreSQL - standard dependency, no new requirements
- **No external APIs**: All calculations are internal

### 4.3 Performance Considerations

1. **Baseline Creation Performance**:
   - Target: < 5 seconds for 20 WBEs, 300 cost elements
   - Optimization: Batch queries, efficient aggregation
   - Monitoring: Add timing logs for baseline creation

2. **Query Performance**:
   - Indexes needed on: `baseline_id`, `wbe_id`, `project_id`
   - Use joins efficiently
   - Consider query plans for large datasets

3. **Memory Usage**:
   - Load all cost elements for project (may be large)
   - Consider pagination or streaming for very large projects
   - Monitor memory usage in tests

### 4.4 Backward Compatibility Requirements

1. **Existing Baselines**:
   - Existing baselines will not have WBE/Project snapshots
   - API endpoints should handle missing snapshots gracefully
   - Consider backfill migration for existing baselines (future work)

2. **API Compatibility**:
   - Existing endpoints must continue to work
   - No breaking changes to existing response schemas
   - New endpoints are additive

3. **Database Compatibility**:
   - Migration is additive (new tables only)
   - No changes to existing tables
   - Migration is reversible

## 5. IMPLEMENTATION NOTES

### 5.1 Calculation Flow

1. **Cost Element Level** (existing):
   - For each cost element, calculate metrics using `get_cost_element_evm_metrics()`
   - Store in `BaselineCostElement`

2. **WBE Level** (new):
   - Group cost elements by WBE
   - For each WBE, aggregate cost element metrics using `aggregate_cost_element_metrics()`
   - Store in `BaselineWBE`

3. **Project Level** (new):
   - Aggregate all WBE metrics using `aggregate_cost_element_metrics()`
   - Store in `BaselineProject`

### 5.2 Time Machine Integration

- Use `baseline_date` as control date for all calculations
- Apply time machine filters when fetching:
  - Cost registrations
  - Earned value entries
  - Forecasts
  - Schedules
- Only include data on or before `baseline_date`

### 5.3 Error Handling

- Validate BaselineLog exists before creating snapshots
- Validate WBE/Project references exist
- Wrap all creation in transaction
- Return clear error messages
- Log errors for debugging

### 5.4 Testing Strategy

- **Unit Tests**: Model creation, helper functions
- **Integration Tests**: Baseline creation flow, API endpoints
- **E2E Tests**: Complete workflow
- **Validation Tests**: Metric accuracy, aggregation consistency
- **Edge Case Tests**: Empty data, None values, large datasets
