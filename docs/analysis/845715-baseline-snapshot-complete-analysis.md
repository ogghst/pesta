# High-Level Analysis: Complete Baseline Snapshot Implementation

**Analysis Date:** 2025-11-29
**Analysis ID:** 845715
**Feature:** Complete Baseline Snapshot at Project, WBE, and Cost Element Levels

## User Story

**As a** Project Manager
**I want** baseline creation to capture complete snapshots of all project data (Project, WBE, and Cost Element levels) with all EVM metrics calculated and stored
**So that** I can perform accurate historical comparisons and variance analysis at any level without recalculating metrics from operational data

## Business Problem

Currently, baseline creation only captures `BaselineCostElement` records (cost element level snapshots). The system lacks:
- Project-level baseline snapshots with aggregated metrics
- WBE-level baseline snapshots with aggregated metrics
- Pre-calculated EVM metrics (CPI, SPI, TCPI, CV, SV) stored at each level
- Immutable snapshot records that preserve the exact state at baseline creation

According to PRD Section 10.1, each baseline must capture "a snapshot of all current budget, cost, revenue, earned value, percent complete, and forecast data for all WBEs and cost elements" with metrics calculated and stored at all hierarchical levels.

## Current Implementation Analysis

### Existing Patterns

1. **BaselineCostElement Model** (`backend/app/models/baseline_cost_element.py`)
   - Stores: `budget_bac`, `revenue_plan`, `actual_ac`, `forecast_eac`, `earned_ev`, `percent_complete`, `planned_value`
   - Uses `VersionStatusMixin` for versioning
   - Foreign key to `BaselineLog` via `baseline_id`
   - Foreign key to `CostElement` via `cost_element_id`

2. **Baseline Creation Function** (`backend/app/api/routes/baseline_logs.py:68-227`)
   - `create_baseline_cost_elements_for_baseline_log()` creates cost element snapshots
   - Aggregates data from `CostRegistration`, `Forecast`, `EarnedValueEntry`
   - Calculates `planned_value` using schedule baseline
   - Does NOT create WBE or Project level snapshots

3. **EVM Metrics Calculation** (`backend/app/services/evm_aggregation.py`)
   - `get_cost_element_evm_metrics()` calculates all EVM metrics for a cost element
   - `aggregate_cost_element_metrics()` aggregates metrics from cost elements to WBE/Project level
   - Returns: `PV`, `EV`, `AC`, `BAC`, `EAC`, `forecasted_quality`, `CPI`, `SPI`, `TCPI`, `CV`, `SV`

4. **Time Machine Pattern** (`backend/app/services/time_machine.py`)
   - `apply_time_machine_filters()` filters records by control date
   - Used throughout for historical data queries

### Missing Components

- **BaselineWBE Model**: No table to store WBE-level baseline snapshots
- **BaselineProject Model**: No table to store project-level baseline snapshots
- **EVM Metrics Storage**: Metrics are calculated on-demand, not stored in baseline snapshots
- **Aggregation Logic**: No baseline-specific aggregation that stores results

## Codebase Pattern Analysis

### Similar Implementations

1. **BaselineCostElement Pattern** (Primary Reference)
   - Location: `backend/app/models/baseline_cost_element.py`
   - Pattern: SQLModel table with `VersionStatusMixin`, foreign keys to parent entities
   - Uses: `create_entity_with_version()` for creation
   - Relationships: `baseline_log`, `cost_element`

2. **EVM Aggregation Service** (Calculation Reference)
   - Location: `backend/app/services/evm_aggregation.py`
   - Pattern: Service functions that calculate metrics from operational data
   - Functions: `get_cost_element_evm_metrics()`, `aggregate_cost_element_metrics()`
   - Returns: Dataclass structures (`CostElementEVMMetrics`, `WBEEVMMetrics`, `ProjectEVMMetrics`)

3. **Entity Versioning Service** (Creation Pattern)
   - Location: `backend/app/services/entity_versioning.py`
   - Pattern: `create_entity_with_version()` handles version/status initialization
   - Used by: All baseline-related entity creation

### Architectural Layers

1. **Models Layer** (`backend/app/models/`)
   - SQLModel-based table definitions
   - Schema classes (Base, Create, Update, Public)
   - VersionStatusMixin for versioning

2. **Services Layer** (`backend/app/services/`)
   - Business logic and calculations
   - Reusable aggregation functions
   - Time machine filtering

3. **API Routes Layer** (`backend/app/api/routes/`)
   - HTTP endpoints
   - Request/response handling
   - Calls service layer functions

## Integration Touchpoint Mapping

### Files Requiring Modification

1. **`backend/app/models/baseline_wbe.py`** (NEW)
   - Create `BaselineWBE` model following `BaselineCostElement` pattern
   - Store: `wbe_id`, `baseline_id`, all EVM metrics (PV, EV, AC, BAC, EAC, CPI, SPI, TCPI, CV, SV)
   - Relationships: `baseline_log`, `wbe`

2. **`backend/app/models/baseline_project.py`** (NEW)
   - Create `BaselineProject` model following `BaselineCostElement` pattern
   - Store: `project_id`, `baseline_id`, all EVM metrics
   - Relationships: `baseline_log`, `project`

3. **`backend/app/api/routes/baseline_logs.py`**
   - Modify `create_baseline_cost_elements_for_baseline_log()` to:
     - Calculate WBE-level metrics and create `BaselineWBE` records
     - Calculate project-level metrics and create `BaselineProject` record
   - Add new endpoints for retrieving WBE and Project baseline snapshots

4. **`backend/app/models/__init__.py`**
   - Export new `BaselineWBE` and `BaselineProject` models
   - Export related schema classes

5. **Database Migration** (NEW)
   - Create Alembic migration for `baseline_wbe` and `baseline_project` tables
   - Add foreign key constraints
   - Add indexes for query performance

### System Dependencies

- **Time Machine**: Must respect `baseline_date` as control date when calculating metrics
- **EVM Aggregation Service**: Reuse existing calculation functions
- **Branch Filtering**: Apply branch filters when fetching operational data for snapshot
- **Status Filtering**: Apply status filters when aggregating operational data

### Configuration Patterns

- No new configuration required
- Uses existing database connection patterns
- Follows existing versioning and status management

## Abstraction Inventory

### Existing Abstractions to Leverage

1. **`VersionStatusMixin`** (`backend/app/models/version_status_mixin.py`)
   - Provides `version`, `status`, `entity_id` fields
   - Used by all baseline models

2. **`create_entity_with_version()`** (`backend/app/services/entity_versioning.py`)
   - Handles entity creation with version initialization
   - Used for all baseline entity creation

3. **`get_cost_element_evm_metrics()`** (`backend/app/services/evm_aggregation.py`)
   - Calculates complete EVM metrics for cost elements
   - Returns `CostElementEVMMetrics` dataclass

4. **`aggregate_cost_element_metrics()`** (`backend/app/services/evm_aggregation.py`)
   - Aggregates cost element metrics to WBE/Project level
   - Returns `WBEEVMMetrics` or `ProjectEVMMetrics`

5. **`apply_time_machine_filters()`** (`backend/app/services/time_machine.py`)
   - Filters records by control date
   - Used when fetching operational data for snapshot

6. **`apply_branch_filters()`** (`backend/app/services/branch_filtering.py`)
   - Filters records by branch
   - Used when fetching operational data

7. **`apply_status_filters()`** (`backend/app/services/branch_filtering.py`)
   - Filters records by status
   - Used when fetching operational data

### Test Utilities

- Existing test fixtures in `backend/tests/conftest.py`
- Test patterns in `backend/tests/api/routes/test_baseline_logs.py`
- Can reuse test data creation helpers

## Alternative Approaches

### Approach 1: Three-Level Snapshot Tables (RECOMMENDED)

**Description:**
Create separate `BaselineWBE` and `BaselineProject` tables following the `BaselineCostElement` pattern. Store all EVM metrics at each level during baseline creation.

**Pros:**
- Consistent with existing `BaselineCostElement` pattern
- Explicit storage of all metrics at each level
- Fast retrieval without recalculation
- Clear data model matching hierarchy
- Supports direct baseline-to-baseline comparisons

**Cons:**
- Requires new database tables and migrations
- More storage space required
- Must maintain consistency across three levels

**Alignment:**
- Perfectly aligns with existing `BaselineCostElement` architecture
- Follows established SQLModel patterns
- Uses existing EVM calculation services

**Complexity:** Medium
- New models: 2 files
- Modified files: 1 route file
- Migration: 1 file
- Estimated LOC: ~400-500

**Risk Factors:**
- Low: Well-established patterns
- Migration complexity: Low (additive only)
- Data consistency: Medium (must calculate correctly)

### Approach 2: Single Baseline Metrics Table with Level Field

**Description:**
Create a single `BaselineMetrics` table with a `level` field (`cost_element`, `wbe`, `project`) and store all metrics in one table.

**Pros:**
- Single table to manage
- Unified query interface
- Potentially simpler aggregation queries

**Cons:**
- Breaks existing pattern (BaselineCostElement is separate)
- More complex foreign key relationships
- Less intuitive data model
- Requires polymorphic relationships

**Alignment:**
- Diverges from existing `BaselineCostElement` pattern
- Would require refactoring existing code

**Complexity:** High
- Requires refactoring existing BaselineCostElement
- More complex relationships
- Estimated LOC: ~600-700

**Risk Factors:**
- High: Breaking change to existing baseline system
- Migration complexity: High (requires data migration)
- Data consistency: Medium

### Approach 3: Store Only Aggregated Values in BaselineLog

**Description:**
Add aggregated metric fields directly to `BaselineLog` table, calculate on creation, store project-level totals only.

**Pros:**
- Minimal schema changes
- Fast project-level baseline retrieval
- Simple implementation

**Cons:**
- No WBE-level baseline snapshots (PRD requirement)
- Cannot compare WBE baselines over time
- Violates PRD Section 10.1 requirement for "all WBEs and cost elements"
- Inconsistent with existing BaselineCostElement pattern

**Alignment:**
- Partially aligns (project level)
- Does not meet PRD requirements

**Complexity:** Low
- Modified files: 1 model, 1 route
- Estimated LOC: ~100-150

**Risk Factors:**
- High: Does not meet PRD requirements
- Missing WBE-level snapshots
- Future maintenance: High (will need to add WBE level later)

## Architectural Impact Assessment

### Architectural Principles

**Follows:**
- **Separation of Concerns**: Models, services, and routes remain separated
- **DRY Principle**: Reuses existing EVM calculation services
- **Consistency**: Follows established `BaselineCostElement` pattern
- **Immutability**: Baseline snapshots are immutable (versioned but not updated)

**Potential Violations:**
- None identified with Approach 1 (recommended)

### Maintenance Burden

**Low Risk Areas:**
- Model definitions follow established patterns
- Service layer reuse minimizes new code
- Calculation logic already exists and tested

**Medium Risk Areas:**
- Must ensure metrics calculated correctly at all levels
- Baseline creation becomes more complex (three-level aggregation)
- Migration must handle existing baselines (may need backfill)

**Future Considerations:**
- Baseline comparison queries will need to join three tables
- Performance: Indexes needed on `baseline_id`, `wbe_id`, `project_id`
- Reporting: May need aggregated views for common queries

### Testing Challenges

1. **Test Data Setup**
   - Must create complete project hierarchy (Project → WBEs → Cost Elements)
   - Must populate operational data (costs, earned value, forecasts)
   - Must verify metrics calculated correctly at each level

2. **Calculation Verification**
   - Verify cost element metrics match operational calculations
   - Verify WBE aggregation matches sum of cost elements
   - Verify project aggregation matches sum of WBEs

3. **Time Machine Testing**
   - Verify baseline uses correct control date
   - Verify only data on/before baseline_date is included

4. **Integration Testing**
   - Test baseline creation end-to-end
   - Test baseline retrieval at all levels
   - Test baseline comparison functionality

## Ambiguities and Missing Information

1. **Existing Baselines**: Should we backfill WBE and Project snapshots for existing baselines?
   - **Recommendation**: Yes, create migration script to calculate and store for existing baselines

2. **Baseline Updates**: Can baselines be updated after creation?
   - **Current Behavior**: Baselines are immutable (versioned)
   - **Recommendation**: Maintain immutability, create new baseline version if needed

3. **Performance Requirements**: Are there performance targets for baseline creation?
   - **Unknown**: Should measure baseline creation time for large projects
   - **Recommendation**: Add performance monitoring, optimize if > 5 seconds

4. **Baseline Deletion**: Can baselines be deleted?
   - **Current Behavior**: Soft delete via `is_cancelled` flag
   - **Recommendation**: Maintain soft delete pattern, cascade to snapshot tables

## Risks and Unknown Factors

1. **Data Consistency Risk**: Medium
   - Must ensure WBE metrics = sum of cost element metrics
   - Must ensure project metrics = sum of WBE metrics
   - **Mitigation**: Add validation tests, use existing aggregation functions

2. **Migration Risk**: Low
   - New tables are additive, no breaking changes
   - Existing baselines may need backfill
   - **Mitigation**: Test migration on staging, provide rollback script

3. **Performance Risk**: Medium
   - Baseline creation may be slow for large projects (many cost elements)
   - **Mitigation**: Batch operations, optimize queries, add indexes

4. **Calculation Accuracy Risk**: Medium
   - Must ensure metrics match operational calculations exactly
   - **Mitigation**: Reuse existing calculation services, comprehensive tests

## Recommended Approach

**Approach 1: Three-Level Snapshot Tables** is recommended because:
- Aligns with existing architecture patterns
- Meets PRD requirements completely
- Maintains consistency with `BaselineCostElement` design
- Provides clear, queryable data model
- Enables efficient baseline comparisons

## Next Steps (After Approval)

1. Create database models (`BaselineWBE`, `BaselineProject`)
2. Create database migration
3. Modify baseline creation function to calculate and store all levels
4. Add API endpoints for retrieving WBE and Project snapshots
5. Write comprehensive tests
6. Create migration script for existing baselines (if needed)
