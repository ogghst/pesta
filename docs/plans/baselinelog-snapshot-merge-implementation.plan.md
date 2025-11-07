# Implementation Plan: PLA-1 Baseline Log and Baseline Snapshot Merge

**Task:** PLA-1 - Merge BaselineSnapshot into BaselineLog
**Status:** Detailed Planning - Ready for Implementation
**Date:** 2025-11-05
**Approach:** Approach 1 - Full Merge (Recommended)

---

## Objective

Merge BaselineSnapshot model into BaselineLog to eliminate architectural duplication, simplify the codebase, and improve performance. This merge will consolidate all baseline-related fields into a single model (BaselineLog) while maintaining all existing functionality and backward compatibility where possible.

---

## Requirements Summary

**From Analysis Document:**
- ✅ **Recommended Approach:** Full Merge (BaselineSnapshot into BaselineLog)
- ✅ **Rationale:** Simplifies architecture, eliminates duplication, improves performance, consistent with codebase patterns
- ✅ **Estimated Effort:** 12-16 hours total (backend 8-10h, frontend 2-3h, testing 2-3h)

**Fields to Merge:**
- `department` (STRING, nullable) - From BaselineSnapshot
- `is_pmb` (BOOLEAN, default=False) - From BaselineSnapshot

**Fields Already Duplicated (will be removed):**
- `baseline_date` - Already in BaselineLog
- `milestone_type` - Already in BaselineLog
- `description` - Already in BaselineLog

**Current State:**
- BaselineLog has: `baseline_id`, `project_id`, `baseline_type`, `baseline_date`, `milestone_type`, `description`, `is_cancelled`, `created_by_id`, `created_at`
- BaselineSnapshot has: `snapshot_id`, `project_id`, `baseline_id` (FK), `baseline_date`, `milestone_type`, `description`, `department`, `is_pmb`, `created_by_id`, `created_at`
- One-to-one relationship: Each BaselineLog has exactly one BaselineSnapshot (created automatically)

---

## Implementation Approach

**Strategy:** Incremental Backend-First TDD Migration
1. **Phase 1:** Add new fields to BaselineLog model (TDD: failing tests first)
2. **Phase 2:** Create database migration (add columns, migrate data)
3. **Phase 3:** Update snapshotting helper function (remove BaselineSnapshot creation)
4. **Phase 4:** Update API endpoints (remove BaselineSnapshot references)
5. **Phase 5:** Update frontend components (rename and update props)
6. **Phase 6:** Regenerate API client and update types
7. **Phase 7:** Update tests (remove BaselineSnapshot tests, update BaselineLog tests)
8. **Phase 8:** Deprecate BaselineSnapshot model (optional, future release)

**TDD Discipline:**
- Write failing tests first for each phase
- Target <100 lines, <5 files per commit
- Comprehensive test coverage for all changes
- No regressions in existing functionality

**Architecture Pattern:**
- Follow existing model update patterns (see CostElement with BudgetAllocation)
- Maintain backward compatibility for API endpoints (keep `/snapshot` endpoint as alias)
- Update schemas following Base/Create/Update/Public pattern

---

## Codebase Pattern Analysis

### Similar Patterns Found

**Pattern 1: Model Field Additions (CostElement with Budget Allocation)**
- **Location:** `backend/app/models/cost_element.py`
- **Pattern:** Added fields to existing model, created migration, updated schemas
- **Reusable:** Follow same pattern for BaselineLog field additions

**Pattern 2: Helper Function Auto-Creation (CostElement with BudgetAllocation)**
- **Location:** `backend/app/api/routes/cost_elements.py` (lines 153-196)
- **Pattern:** `create_budget_allocation_for_cost_element()` helper function
- **Reusable:** Pattern for refactoring `create_baseline_snapshot_for_baseline_log()` to create BaselineCostElement directly

**Pattern 3: API Endpoint Aliases**
- **Location:** Various routes
- **Pattern:** Maintain backward compatibility with endpoint aliases
- **Reusable:** Keep `/snapshot` endpoint as alias to `/summary` for BaselineLog

---

## Integration Touchpoint Mapping

### Backend Files Requiring Modification

1. **`backend/app/models/baseline_log.py`**
   - Add `department` field (STRING, nullable, max_length=100)
   - Add `is_pmb` field (BOOLEAN, default=False)
   - Update Base/Create/Update/Public schemas
   - **Impact:** Model changes require migration

2. **`backend/app/models/baseline_snapshot.py`**
   - **Deprecation:** Mark as deprecated (keep for backward compatibility during transition)
   - **Future:** Remove in next major release
   - **Impact:** Model will not be used but kept for data migration reference

3. **`backend/app/api/routes/baseline_logs.py`**
   - Update `create_baseline_snapshot_for_baseline_log()` → `create_baseline_cost_elements_for_baseline_log()`
   - Remove BaselineSnapshot creation logic
   - Update `POST /baseline-logs/` to not create BaselineSnapshot
   - Update `GET /baseline-logs/{baseline_id}/snapshot` to return BaselineLog data (or rename to `/summary`)
   - **Impact:** Helper function refactoring, endpoint updates

4. **Database Migration (Alembic)**
   - Add `department` column to `baselinelog` table (nullable)
   - Add `is_pmb` column to `baselinelog` table (default=False)
   - Data migration: Copy `department` and `is_pmb` from BaselineSnapshot to BaselineLog (one-to-one)
   - **Impact:** Requires data migration script

5. **Test Files:**
   - `backend/tests/models/test_baseline_log.py` - Add tests for new fields
   - `backend/tests/api/routes/test_baseline_logs.py` - Update snapshot endpoint tests
   - `backend/tests/api/routes/test_baseline_snapshot_summary.py` - Update to use BaselineLog
   - **Impact:** Test updates required

### Frontend Files Requiring Modification

1. **`frontend/src/components/Projects/ViewBaselineSnapshot.tsx`**
   - Rename to `ViewBaseline.tsx` or `BaselineDetail.tsx`
   - Update props: use `BaselineLogPublic` instead of separate snapshot
   - Update API calls to use BaselineLog endpoint
   - **Impact:** Component rename and prop updates

2. **`frontend/src/components/Projects/BaselineSnapshotSummary.tsx`**
   - Rename to `BaselineSummary.tsx`
   - Update props: use `BaselineLogPublic` instead of `BaselineSnapshotSummaryPublic`
   - Update API calls (may need schema update)
   - **Impact:** Component rename and API update

3. **`frontend/src/components/Projects/BaselineLogsTable.tsx`**
   - Update to use renamed ViewBaseline component
   - No structural changes needed
   - **Impact:** Import path update

4. **`frontend/src/client/types.gen.ts`**
   - Regenerate after backend model changes
   - `BaselineSnapshotPublic` may be removed or deprecated
   - `BaselineLogPublic` will include `department` and `is_pmb`
   - **Impact:** Type updates after client regeneration

5. **`frontend/src/client/services/BaselineLogsService.ts`**
   - Regenerate after backend API changes
   - Snapshot endpoint may be renamed or removed
   - **Impact:** Service method updates after client regeneration

---

## Phase Breakdown

### Phase 1: Model Updates and Schema Changes (Backend) - 2 hours

**Objective:** Add `department` and `is_pmb` fields to BaselineLog model with proper schemas.

**TDD Approach:**
1. Write failing tests for new fields in `test_baseline_log.py`
2. Update `BaselineLogBase` schema to include `department` and `is_pmb`
3. Update `BaselineLogCreate` schema
4. Update `BaselineLogUpdate` schema
5. Update `BaselineLogPublic` schema
6. Update `BaselineLog` model (table=True)
7. Run tests to verify green

**Files to Modify:**
- `backend/app/models/baseline_log.py` (1 file)
- `backend/tests/models/test_baseline_log.py` (1 file)

**Test Checklist:**
- ✅ Test BaselineLog creation with `department` field
- ✅ Test BaselineLog creation with `is_pmb` field
- ✅ Test BaselineLog creation with both fields
- ✅ Test BaselineLog update with `department`
- ✅ Test BaselineLog update with `is_pmb`
- ✅ Test BaselineLogPublic includes new fields

**Commit Strategy:**
- Commit 1: Add failing tests (<50 lines)
- Commit 2: Update schemas (<100 lines)
- Commit 3: Update model (<50 lines)

---

### Phase 2: Database Migration (Backend) - 2 hours

**Objective:** Create Alembic migration to add new columns and migrate existing data.

**TDD Approach:**
1. Create Alembic migration script
2. Add `department` column (nullable, VARCHAR(100))
3. Add `is_pmb` column (BOOLEAN, default=False)
4. Data migration: Copy values from BaselineSnapshot to BaselineLog (one-to-one join)
5. Test migration up/down

**Migration Strategy:**
```python
# Migration: add_department_and_is_pmb_to_baseline_log
def upgrade():
    # Add columns
    op.add_column('baselinelog', sa.Column('department', sa.String(100), nullable=True))
    op.add_column('baselinelog', sa.Column('is_pmb', sa.Boolean(), nullable=False, server_default='false'))

    # Data migration: Copy from BaselineSnapshot
    connection = op.get_bind()
    connection.execute(
        text("""
            UPDATE baselinelog bl
            SET department = bs.department,
                is_pmb = bs.is_pmb
            FROM baselinesnapshot bs
            WHERE bl.baseline_id = bs.baseline_id
        """)
    )

def downgrade():
    op.drop_column('baselinelog', 'department')
    op.drop_column('baselinelog', 'is_pmb')
```

**Files to Create:**
- `backend/alembic/versions/XXXX_add_department_and_is_pmb_to_baseline_log.py`

**Test Checklist:**
- ✅ Migration applies successfully
- ✅ Data migration copies values correctly
- ✅ Migration can be rolled back
- ✅ Null values handled correctly (if BaselineSnapshot doesn't exist)

**Commit Strategy:**
- Commit 1: Create migration script (<100 lines)

---

### Phase 3: Helper Function Refactoring (Backend) - 2 hours

**Objective:** Refactor `create_baseline_snapshot_for_baseline_log()` to create BaselineCostElement directly without BaselineSnapshot.

**TDD Approach:**
1. Write failing tests for refactored helper function
2. Rename function: `create_baseline_snapshot_for_baseline_log()` → `create_baseline_cost_elements_for_baseline_log()`
3. Remove BaselineSnapshot creation logic
4. Keep BaselineCostElement creation logic (unchanged)
5. Update function signature to accept `department` and `is_pmb` (optional)
6. Update function to set `department` and `is_pmb` on BaselineLog instead of creating BaselineSnapshot
7. Run tests to verify green

**Files to Modify:**
- `backend/app/api/routes/baseline_logs.py` (1 file)
- `backend/tests/api/routes/test_baseline_logs.py` (1 file)

**Function Signature Change:**
```python
# OLD
def create_baseline_snapshot_for_baseline_log(
    session: Session,
    baseline_log: BaselineLog,
    created_by_id: uuid.UUID,
) -> BaselineSnapshot:

# NEW
def create_baseline_cost_elements_for_baseline_log(
    session: Session,
    baseline_log: BaselineLog,
    created_by_id: uuid.UUID,
    department: str | None = None,
    is_pmb: bool = False,
) -> None:
    # Sets department and is_pmb on baseline_log
    # Creates BaselineCostElement records
```

**Test Checklist:**
- ✅ Helper function creates BaselineCostElement records
- ✅ Helper function sets `department` on BaselineLog
- ✅ Helper function sets `is_pmb` on BaselineLog
- ✅ Helper function does NOT create BaselineSnapshot
- ✅ BaselineCostElement records linked to BaselineLog correctly

**Commit Strategy:**
- Commit 1: Add failing tests (<50 lines)
- Commit 2: Refactor helper function (<100 lines)
- Commit 3: Update tests to pass (<50 lines)

---

### Phase 4: API Endpoint Updates (Backend) - 2 hours

**Objective:** Update API endpoints to use BaselineLog directly instead of BaselineSnapshot.

**TDD Approach:**
1. Write failing tests for updated endpoints
2. Update `POST /baseline-logs/` to accept `department` and `is_pmb` in request body
3. Update `POST /baseline-logs/` to call refactored helper function
4. Update `GET /baseline-logs/{baseline_id}/snapshot` to return BaselineLog data (or rename to `/summary`)
5. Update `BaselineSnapshotSummaryPublic` schema to use BaselineLog fields (or create new `BaselineLogSummaryPublic`)
6. Run tests to verify green

**Files to Modify:**
- `backend/app/api/routes/baseline_logs.py` (1 file)
- `backend/app/models/baseline_log.py` (schema updates)
- `backend/tests/api/routes/test_baseline_logs.py` (1 file)
- `backend/tests/api/routes/test_baseline_snapshot_summary.py` (1 file)

**Endpoint Changes:**
- `POST /baseline-logs/` - Add `department` and `is_pmb` to request body
- `GET /baseline-logs/{baseline_id}/snapshot` - Return BaselineLog data (keep as alias for backward compatibility)
- `GET /baseline-logs/{baseline_id}/summary` - New endpoint (optional, or use `/snapshot` as alias)

**Schema Updates:**
- `BaselineLogCreate` - Add `department` and `is_pmb` fields (optional)
- `BaselineLogUpdate` - Add `department` and `is_pmb` fields (optional)
- `BaselineLogPublic` - Already includes new fields from Phase 1
- `BaselineSnapshotSummaryPublic` - Update to use BaselineLog fields (or deprecate)

**Test Checklist:**
- ✅ POST endpoint accepts `department` and `is_pmb`
- ✅ POST endpoint creates BaselineLog with new fields
- ✅ POST endpoint does NOT create BaselineSnapshot
- ✅ GET `/snapshot` endpoint returns BaselineLog data
- ✅ Summary endpoint returns correct aggregated values
- ✅ All existing endpoint tests still pass

**Commit Strategy:**
- Commit 1: Update POST endpoint (<100 lines)
- Commit 2: Update GET snapshot endpoint (<50 lines)
- Commit 3: Update summary schema and endpoint (<100 lines)

---

### Phase 5: Frontend Component Updates (Frontend) - 2-3 hours

**Objective:** Update frontend components to use BaselineLog instead of BaselineSnapshot.

**TDD Approach:**
1. Update component imports and types
2. Rename ViewBaselineSnapshot → ViewBaseline
3. Update component props to use BaselineLogPublic
4. Update API service calls
5. Update component names in BaselineLogsTable
6. Rename BaselineSnapshotSummary → BaselineSummary
7. Update summary component props
8. Test manually (frontend tests optional)

**Files to Modify:**
- `frontend/src/components/Projects/ViewBaselineSnapshot.tsx` → `ViewBaseline.tsx` (rename)
- `frontend/src/components/Projects/BaselineSnapshotSummary.tsx` → `BaselineSummary.tsx` (rename)
- `frontend/src/components/Projects/BaselineLogsTable.tsx` (1 file)
- Update imports in project detail page if needed

**Component Changes:**
- `ViewBaselineSnapshot` → `ViewBaseline`
- Props: `baseline_id: UUID` instead of separate baseline/snapshot
- API calls: Use BaselineLog endpoints instead of snapshot endpoints
- `BaselineSnapshotSummary` → `BaselineSummary`
- Props: Use `BaselineLogPublic` instead of `BaselineSnapshotSummaryPublic`

**Test Checklist:**
- ✅ ViewBaseline component renders correctly
- ✅ BaselineSummary component displays correct data
- ✅ BaselineLogsTable opens ViewBaseline modal correctly
- ✅ All tabs in ViewBaseline work (Summary, By WBE, All Cost Elements)
- ✅ No TypeScript errors

**Commit Strategy:**
- Commit 1: Rename ViewBaselineSnapshot → ViewBaseline (<100 lines)
- Commit 2: Update ViewBaseline props and API calls (<100 lines)
- Commit 3: Rename BaselineSnapshotSummary → BaselineSummary (<50 lines)
- Commit 4: Update BaselineLogsTable imports (<20 lines)

---

### Phase 6: API Client Regeneration (Frontend) - 15 minutes

**Objective:** Regenerate OpenAPI client after backend changes.

**TDD Approach:**
1. Run backend server to generate updated OpenAPI spec
2. Regenerate frontend client using OpenAPI generator
3. Verify TypeScript compilation passes
4. Update any broken imports

**Files to Modify:**
- `frontend/src/client/types.gen.ts` (regenerated)
- `frontend/src/client/services/BaselineLogsService.ts` (regenerated)
- `frontend/src/client/schemas.gen.ts` (regenerated)

**Commands:**
```bash
# Backend: Ensure server is running
cd backend && uvicorn app.main:app --reload

# Frontend: Regenerate client
cd frontend && npm run generate-client
```

**Test Checklist:**
- ✅ TypeScript compilation passes
- ✅ No type errors in components
- ✅ Service methods updated correctly
- ✅ All imports resolve correctly

**Commit Strategy:**
- Commit 1: Regenerate client and fix imports (<20 lines)

---

### Phase 7: Test Updates and Cleanup (Backend) - 2 hours

**Objective:** Update all tests to remove BaselineSnapshot references and verify BaselineLog functionality.

**TDD Approach:**
1. Update test imports (remove BaselineSnapshot imports)
2. Update test fixtures to create BaselineLog with new fields
3. Update test assertions to check BaselineLog fields instead of BaselineSnapshot
4. Remove BaselineSnapshot-specific tests
5. Add new tests for BaselineLog `department` and `is_pmb` fields
6. Run full test suite to verify no regressions

**Files to Modify:**
- `backend/tests/models/test_baseline_log.py` (1 file)
- `backend/tests/api/routes/test_baseline_logs.py` (1 file)
- `backend/tests/api/routes/test_baseline_snapshot_summary.py` (1 file - rename or update)
- `backend/tests/api/routes/test_baseline_cost_elements_by_wbe.py` (1 file)
- `backend/tests/api/routes/test_baseline_cost_elements_list.py` (1 file)

**Test Updates:**
- Remove `BaselineSnapshot` imports
- Update helper function calls: `create_baseline_snapshot_for_baseline_log()` → `create_baseline_cost_elements_for_baseline_log()`
- Update assertions: Check BaselineLog fields instead of BaselineSnapshot
- Add tests for `department` and `is_pmb` fields

**Test Checklist:**
- ✅ All BaselineLog tests pass
- ✅ All API endpoint tests pass
- ✅ All snapshot summary tests updated and pass
- ✅ No BaselineSnapshot references in tests
- ✅ Full test suite passes (no regressions)

**Commit Strategy:**
- Commit 1: Update test imports and fixtures (<100 lines)
- Commit 2: Update test assertions (<100 lines)
- Commit 3: Add new field tests (<50 lines)

---

### Phase 8: Deprecation and Cleanup (Optional, Future) - 1 hour

**Objective:** Mark BaselineSnapshot model as deprecated and plan removal in future release.

**TDD Approach:**
1. Add deprecation warnings to BaselineSnapshot model
2. Update documentation to use BaselineLog only
3. Add TODO comments for future removal
4. Create migration plan for removing BaselineSnapshot table (future release)

**Files to Modify:**
- `backend/app/models/baseline_snapshot.py` (add deprecation docstring)
- `docs/` (update documentation)

**Deprecation Strategy:**
- Keep BaselineSnapshot model for reference during transition
- Mark with deprecation warning in docstring
- Remove in next major version release
- Create migration to drop BaselineSnapshot table (future)

**Test Checklist:**
- ✅ Deprecation warnings added
- ✅ Documentation updated
- ✅ No functional impact

**Commit Strategy:**
- Commit 1: Add deprecation warnings and update docs (<50 lines)

---

## Risk Mitigation

### Known Risks

1. **Data Migration Risk (Medium)**
   - **Risk:** Data loss if migration fails or BaselineSnapshot has unexpected data
   - **Mitigation:**
     - Create comprehensive data migration script with validation
     - Test migration on development database first
     - Create rollback script
     - Verify data integrity after migration

2. **Breaking API Changes (Low)**
   - **Risk:** External consumers may depend on BaselineSnapshot endpoints
   - **Mitigation:**
     - Keep `/snapshot` endpoint as alias for backward compatibility
     - Update API documentation
     - Provide migration guide for external consumers

3. **Frontend Component Updates (Low)**
   - **Risk:** Component renames may introduce bugs
   - **Mitigation:**
     - Comprehensive manual testing
     - Update all import paths
     - Verify TypeScript compilation

### Unknown Factors

1. **Production Data Volume**
   - **Unknown:** How many BaselineSnapshot records exist?
   - **Action:** Query production database before migration

2. **External API Consumers**
   - **Unknown:** Are there external systems using snapshot endpoints?
   - **Action:** Check API logs and documentation

---

## Acceptance Criteria

### Functional Requirements

- ✅ BaselineLog model includes `department` and `is_pmb` fields
- ✅ BaselineLog creation accepts `department` and `is_pmb` in request body
- ✅ BaselineCostElement records created correctly (no BaselineSnapshot)
- ✅ All API endpoints return BaselineLog data (no BaselineSnapshot)
- ✅ Frontend components use BaselineLog (no BaselineSnapshot references)
- ✅ All existing functionality preserved

### Non-Functional Requirements

- ✅ No regressions in existing tests
- ✅ Database migration applies successfully
- ✅ TypeScript compilation passes
- ✅ All tests pass (backend + frontend)
- ✅ API backward compatibility maintained (endpoint aliases)

---

## Implementation Checklist

### Backend
- [ ] Phase 1: Model updates and schema changes
- [ ] Phase 2: Database migration
- [ ] Phase 3: Helper function refactoring
- [ ] Phase 4: API endpoint updates
- [ ] Phase 7: Test updates and cleanup
- [ ] Phase 8: Deprecation (optional)

### Frontend
- [ ] Phase 5: Component updates
- [ ] Phase 6: API client regeneration

### Testing
- [ ] All backend tests pass
- [ ] All frontend TypeScript compilation passes
- [ ] Manual testing of all baseline functionality
- [ ] No regressions in existing features

---

## Estimated Effort

**Backend:** 8-10 hours
- Phase 1: 2 hours
- Phase 2: 2 hours
- Phase 3: 2 hours
- Phase 4: 2 hours
- Phase 7: 2 hours
- Phase 8: 1 hour (optional)

**Frontend:** 2-3 hours
- Phase 5: 2-3 hours
- Phase 6: 15 minutes

**Total:** 12-16 hours

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Confirm no external API consumers** of BaselineSnapshot endpoints
3. **Query production database** to assess BaselineSnapshot data volume
4. **Begin Phase 1** with failing tests (TDD approach)

---

**Document Owner:** Development Team
**Review Frequency:** Before implementation begins
