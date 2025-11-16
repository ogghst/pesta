# Implementation Plan: E4-003 EVM Performance Indices (CPI, SPI, TCPI)

**Task:** E4-003 - EVM Performance Indices
**Sprint:** Sprint 4 - Earned Value Recording and Core EVM Calculations
**Status:** Planning Complete - Ready for Implementation
**Date:** 2025-11-16
**Current Time:** 20:36 CET (Europe/Rome)

---

## WORKING AGREEMENTS ACKNOWLEDGMENT

✅ **Test-Driven Development (TDD):** All code changes must be preceded by failing tests
✅ **Incremental Change:** Small, atomic commits (<100 lines, <5 files target)
✅ **Architectural Respect:** Follow existing patterns and abstractions (mirror E4-001 PV and E4-002 EV patterns)
✅ **No Code Duplication:** Reuse existing implementations where possible

---

## Objective

Implement EVM Performance Indices calculation engine computing CPI, SPI, and TCPI at project and WBE levels (cost element optional) using existing PV, EV, AC, and BAC inputs. This follows the E4-001 Planned Value and E4-002 Earned Value patterns and enables performance analysis for project managers.

---

## Requirements Summary

**From Analysis Document:**
- ✅ **Recommended Approach:** Dedicated EVM indices service and router (mirror PV/EV architecture)
- ✅ **Required Levels:** Project and WBE levels (cost element level optional in MVP)
- ✅ **Edge Case Rules:**
  - CPI = undefined (None) when AC = 0 and EV > 0
  - SPI = null (None) when PV = 0
  - TCPI = 'overrun' (string literal) when BAC ≤ AC
- ✅ **Input Sources:** Leverage existing PV, EV, AC, and BAC endpoints/services
- ✅ **Time-Machine Integration:** All indices computed as-of control date

**Key Business Rules:**
- CPI = EV / AC (undefined when AC = 0 and EV > 0)
- SPI = EV / PV (null when PV = 0)
- TCPI = (BAC - EV) / (BAC - AC) (returns 'overrun' when BAC ≤ AC)
- Indices computed at project and WBE levels using aggregated PV, EV, AC, BAC
- All calculations respect time-machine control date

---

## Implementation Approach

**Strategy:** Incremental Backend-First TDD (mirror E4-001/E4-002 pattern)
1. **Phase 1:** Service layer - Pure calculation functions (TDD: failing tests first)
2. **Phase 2:** Response models - Schema definitions with proper types
3. **Phase 3:** API routes - FastAPI endpoints for project and WBE levels
4. **Phase 4:** Router registration - Wire up API routes
5. **Phase 5:** Integration testing - Verify end-to-end behavior

**Architecture Pattern:**
- Service layer: Pure functions (no database access) - `backend/app/services/evm_indices.py`
- API layer: FastAPI routes with queries - `backend/app/api/routes/evm_indices.py`
- Models layer: Response schemas - `backend/app/models/evm_indices.py`
- Tests: Service unit tests + API integration tests

---

## IMPLEMENTATION STEPS

### PHASE 1: Service Layer (Backend)

#### Step 1.1: Create Service Module Structure

**Objective:** Create service module with constants and helper functions following PV/EV pattern.

**Acceptance Criteria:**
- ✅ `backend/app/services/evm_indices.py` exists
- ✅ Constants defined: `TWO_PLACES`, `FOUR_PLACES`, `ZERO`, `ONE`
- ✅ `_quantize()` helper function implemented
- ✅ `EVMIndicesError` exception class defined
- ✅ File imports correctly (no syntax errors)

**Test-First Requirement:**
- None (infrastructure setup, no business logic yet)

**Files to Create:**
- `backend/app/services/evm_indices.py`

**Dependencies:**
- None

**Estimated Time:** 15 minutes

---

#### Step 1.2: Implement CPI Calculation Function

**Objective:** Create function to calculate Cost Performance Index (CPI) = EV / AC with edge case handling.

**Acceptance Criteria:**
- ✅ `calculate_cpi()` function exists
- ✅ Returns `Decimal` when AC > 0
- ✅ Returns `None` when AC = 0 and EV > 0 (undefined case)
- ✅ Returns `None` when AC = 0 and EV = 0 (undefined case)
- ✅ Returns quantized value to 4 decimal places when defined
- ✅ Handles negative values appropriately

**Test-First Requirement:**
- Create test: `test_calculate_cpi_normal_case()` - EV=100, AC=80 → CPI=1.25
- Create test: `test_calculate_cpi_undefined_ac_zero_ev_positive()` - AC=0, EV=50 → None
- Create test: `test_calculate_cpi_undefined_ac_zero_ev_zero()` - AC=0, EV=0 → None
- Create test: `test_calculate_cpi_quantization()` - Verify 4 decimal places
- Create test: `test_calculate_cpi_negative_values()` - Handle negative AC/EV appropriately

**Files to Create:**
- `backend/tests/services/test_evm_indices.py` (if not exists)

**Files to Modify:**
- `backend/app/services/evm_indices.py`

**Dependencies:**
- Step 1.1

**Estimated Time:** 1-2 hours

---

#### Step 1.3: Implement SPI Calculation Function

**Objective:** Create function to calculate Schedule Performance Index (SPI) = EV / PV with edge case handling.

**Acceptance Criteria:**
- ✅ `calculate_spi()` function exists
- ✅ Returns `Decimal` when PV > 0
- ✅ Returns `None` when PV = 0 (null case per business rule)
- ✅ Returns quantized value to 4 decimal places when defined
- ✅ Handles negative values appropriately

**Test-First Requirement:**
- Create test: `test_calculate_spi_normal_case()` - EV=80, PV=100 → SPI=0.80
- Create test: `test_calculate_spi_null_pv_zero()` - PV=0, EV=50 → None
- Create test: `test_calculate_spi_quantization()` - Verify 4 decimal places
- Create test: `test_calculate_spi_negative_values()` - Handle negative PV/EV appropriately

**Files to Modify:**
- `backend/app/services/evm_indices.py`
- `backend/tests/services/test_evm_indices.py`

**Dependencies:**
- Step 1.2

**Estimated Time:** 1-2 hours

---

#### Step 1.4: Implement TCPI Calculation Function

**Objective:** Create function to calculate To-Complete Performance Index (TCPI) = (BAC - EV) / (BAC - AC) with edge case handling.

**Acceptance Criteria:**
- ✅ `calculate_tcpi()` function exists
- ✅ Returns `Decimal` when BAC > AC
- ✅ Returns `'overrun'` (string literal) when BAC ≤ AC (per business rule)
- ✅ Returns `None` when BAC = AC = 0 (undefined case)
- ✅ Returns quantized value to 4 decimal places when defined
- ✅ Handles negative values appropriately

**Test-First Requirement:**
- Create test: `test_calculate_tcpi_normal_case()` - BAC=1000, EV=600, AC=800 → TCPI=0.50
- Create test: `test_calculate_tcpi_overrun_bac_equals_ac()` - BAC=1000, AC=1000 → 'overrun'
- Create test: `test_calculate_tcpi_overrun_bac_less_than_ac()` - BAC=800, AC=1000 → 'overrun'
- Create test: `test_calculate_tcpi_undefined_bac_ac_zero()` - BAC=0, AC=0 → None
- Create test: `test_calculate_tcpi_quantization()` - Verify 4 decimal places
- Create test: `test_calculate_tcpi_negative_values()` - Handle negative values appropriately

**Files to Modify:**
- `backend/app/services/evm_indices.py`
- `backend/tests/services/test_evm_indices.py`

**Dependencies:**
- Step 1.3

**Estimated Time:** 1-2 hours

---

#### Step 1.5: Implement Aggregation Helper

**Objective:** Create helper function to aggregate EVM indices across multiple cost elements (for WBE/project levels).

**Acceptance Criteria:**
- ✅ `aggregate_evm_indices()` function exists
- ✅ Takes iterable of (PV, EV, AC, BAC) tuples
- ✅ Returns aggregated totals for PV, EV, AC, BAC
- ✅ Handles empty input gracefully (returns zeros)
- ✅ Returns `AggregateResult` dataclass

**Test-First Requirement:**
- Create test: `test_aggregate_evm_indices_multiple_elements()` - Verify correct summation
- Create test: `test_aggregate_evm_indices_empty()` - Returns zeros
- Create test: `test_aggregate_evm_indices_single_element()` - Single element aggregation
- Create test: `test_aggregate_evm_indices_quantization()` - Verify quantization

**Files to Modify:**
- `backend/app/services/evm_indices.py`
- `backend/tests/services/test_evm_indices.py`

**Dependencies:**
- Steps 1.2, 1.3, 1.4

**Estimated Time:** 1 hour

---

### PHASE 2: Response Models (Backend)

#### Step 2.1: Create EVM Indices Response Models

**Objective:** Define response schemas for EVM indices following PV/EV model patterns.

**Acceptance Criteria:**
- ✅ `EVMIndicesBase` base schema exists
- ✅ `EVMIndicesWBEPublic` schema exists (WBE level)
- ✅ `EVMIndicesProjectPublic` schema exists (project level)
- ✅ All schemas include: `cpi`, `spi`, `tcpi`, `pv`, `ev`, `ac`, `bac`
- ✅ CPI, SPI, TCPI fields are `Decimal | None` or `Decimal | Literal['overrun'] | None`
- ✅ PV, EV, AC, BAC fields are `Decimal`
- ✅ Control date and level fields included
- ✅ Models exported in `backend/app/models/__init__.py`

**Test-First Requirement:**
- None (schema definitions, tested via API tests)

**Files to Create:**
- `backend/app/models/evm_indices.py`

**Files to Modify:**
- `backend/app/models/__init__.py`

**Dependencies:**
- Phase 1 complete

**Estimated Time:** 30 minutes

---

### PHASE 3: API Routes (Backend)

#### Step 3.1: Create API Router Structure

**Objective:** Create FastAPI router with helper functions following PV/EV pattern.

**Acceptance Criteria:**
- ✅ `backend/app/api/routes/evm_indices.py` exists
- ✅ Router created with prefix `/projects` and tag `evm-indices`
- ✅ `_ensure_project_exists()` helper function exists
- ✅ `_ensure_wbe_exists()` helper function exists
- ✅ Helper functions use time-machine control date filtering

**Test-First Requirement:**
- None (infrastructure setup)

**Files to Create:**
- `backend/app/api/routes/evm_indices.py`

**Dependencies:**
- Phase 2 complete

**Estimated Time:** 30 minutes

---

#### Step 3.2: Implement Helper to Fetch PV/EV/AC/BAC for WBE

**Objective:** Create helper function to aggregate PV, EV, AC, and BAC for a WBE at control date.

**Acceptance Criteria:**
- ✅ `_get_wbe_evm_inputs()` function exists
- ✅ Queries all cost elements for WBE (respecting control date)
- ✅ Fetches PV using planned_value service/endpoint pattern
- ✅ Fetches EV using earned_value service/endpoint pattern
- ✅ Fetches AC using cost_summary service/endpoint pattern
- ✅ Fetches BAC from cost element budgets
- ✅ Returns tuple of (PV, EV, AC, BAC) as Decimals
- ✅ Handles empty WBE gracefully (returns zeros)

**Test-First Requirement:**
- Create test: `test_get_wbe_evm_inputs_normal_case()` - Verify correct aggregation
- Create test: `test_get_wbe_evm_inputs_empty_wbe()` - Returns zeros
- Create test: `test_get_wbe_evm_inputs_respects_control_date()` - Time-machine filtering

**Files to Modify:**
- `backend/app/api/routes/evm_indices.py`
- `backend/tests/api/routes/test_evm_indices.py` (create if not exists)

**Dependencies:**
- Step 3.1

**Estimated Time:** 2-3 hours

---

#### Step 3.3: Implement Helper to Fetch PV/EV/AC/BAC for Project

**Objective:** Create helper function to aggregate PV, EV, AC, and BAC for a project at control date.

**Acceptance Criteria:**
- ✅ `_get_project_evm_inputs()` function exists
- ✅ Queries all WBEs for project (respecting control date)
- ✅ Aggregates PV, EV, AC, BAC across all WBEs
- ✅ Returns tuple of (PV, EV, AC, BAC) as Decimals
- ✅ Handles empty project gracefully (returns zeros)

**Test-First Requirement:**
- Create test: `test_get_project_evm_inputs_normal_case()` - Verify correct aggregation
- Create test: `test_get_project_evm_inputs_empty_project()` - Returns zeros
- Create test: `test_get_project_evm_inputs_multiple_wbes()` - Aggregation across WBEs
- Create test: `test_get_project_evm_inputs_respects_control_date()` - Time-machine filtering

**Files to Modify:**
- `backend/app/api/routes/evm_indices.py`
- `backend/tests/api/routes/test_evm_indices.py`

**Dependencies:**
- Step 3.2

**Estimated Time:** 2-3 hours

---

#### Step 3.4: Implement WBE-Level EVM Indices Endpoint

**Objective:** Create API endpoint to return CPI, SPI, TCPI for a WBE.

**Acceptance Criteria:**
- ✅ `GET /projects/{project_id}/evm-indices/wbes/{wbe_id}` endpoint exists
- ✅ Uses time-machine control date dependency
- ✅ Validates project and WBE exist
- ✅ Calls `_get_wbe_evm_inputs()` to get PV, EV, AC, BAC
- ✅ Calls service functions to calculate CPI, SPI, TCPI
- ✅ Returns `EVMIndicesWBEPublic` response
- ✅ Handles 404 for non-existent WBE
- ✅ Handles edge cases (None values, 'overrun' for TCPI)

**Test-First Requirement:**
- Create test: `test_get_wbe_evm_indices_normal_case()` - All indices defined
- Create test: `test_get_wbe_evm_indices_cpi_undefined()` - AC=0, EV>0 → CPI=None
- Create test: `test_get_wbe_evm_indices_spi_null()` - PV=0 → SPI=None
- Create test: `test_get_wbe_evm_indices_tcpi_overrun()` - BAC≤AC → TCPI='overrun'
- Create test: `test_get_wbe_evm_indices_not_found()` - 404 for non-existent WBE
- Create test: `test_get_wbe_evm_indices_respects_control_date()` - Time-machine filtering

**Files to Modify:**
- `backend/app/api/routes/evm_indices.py`
- `backend/tests/api/routes/test_evm_indices.py`

**Dependencies:**
- Steps 3.2, 3.3

**Estimated Time:** 2-3 hours

---

#### Step 3.5: Implement Project-Level EVM Indices Endpoint

**Objective:** Create API endpoint to return CPI, SPI, TCPI for a project.

**Acceptance Criteria:**
- ✅ `GET /projects/{project_id}/evm-indices` endpoint exists
- ✅ Uses time-machine control date dependency
- ✅ Validates project exists
- ✅ Calls `_get_project_evm_inputs()` to get PV, EV, AC, BAC
- ✅ Calls service functions to calculate CPI, SPI, TCPI
- ✅ Returns `EVMIndicesProjectPublic` response
- ✅ Handles 404 for non-existent project
- ✅ Handles edge cases (None values, 'overrun' for TCPI)

**Test-First Requirement:**
- Create test: `test_get_project_evm_indices_normal_case()` - All indices defined
- Create test: `test_get_project_evm_indices_cpi_undefined()` - AC=0, EV>0 → CPI=None
- Create test: `test_get_project_evm_indices_spi_null()` - PV=0 → SPI=None
- Create test: `test_get_project_evm_indices_tcpi_overrun()` - BAC≤AC → TCPI='overrun'
- Create test: `test_get_project_evm_indices_not_found()` - 404 for non-existent project
- Create test: `test_get_project_evm_indices_respects_control_date()` - Time-machine filtering
- Create test: `test_get_project_evm_indices_multiple_wbes()` - Aggregation across WBEs

**Files to Modify:**
- `backend/app/api/routes/evm_indices.py`
- `backend/tests/api/routes/test_evm_indices.py`

**Dependencies:**
- Step 3.4

**Estimated Time:** 2-3 hours

---

### PHASE 4: Router Registration (Backend)

#### Step 4.1: Register EVM Indices Router

**Objective:** Wire up the EVM indices router in the main API application.

**Acceptance Criteria:**
- ✅ Router imported in `backend/app/api/main.py`
- ✅ Router registered with app
- ✅ No import errors or circular dependencies
- ✅ API endpoints accessible at expected paths

**Test-First Requirement:**
- None (integration, tested via API tests)

**Files to Modify:**
- `backend/app/api/main.py`

**Dependencies:**
- Phase 3 complete

**Estimated Time:** 15 minutes

---

### PHASE 5: Integration Testing and Validation

#### Step 5.1: End-to-End Integration Tests

**Objective:** Verify complete end-to-end behavior with realistic data scenarios.

**Acceptance Criteria:**
- ✅ Test with real project/WBE/cost element data
- ✅ Test with multiple cost elements per WBE
- ✅ Test with multiple WBEs per project
- ✅ Test time-machine control date changes
- ✅ Test all edge cases in realistic scenarios
- ✅ Verify response schemas match OpenAPI spec
- ✅ All tests passing

**Test-First Requirement:**
- Create test: `test_wbe_evm_indices_integration()` - Full WBE scenario
- Create test: `test_project_evm_indices_integration()` - Full project scenario
- Create test: `test_evm_indices_time_machine_integration()` - Control date changes
- Create test: `test_evm_indices_edge_cases_integration()` - All edge cases together

**Files to Modify:**
- `backend/tests/api/routes/test_evm_indices.py`

**Dependencies:**
- Phase 4 complete

**Estimated Time:** 2-3 hours

---

#### Step 5.2: Regenerate OpenAPI Client

**Objective:** Regenerate frontend API client to include new EVM indices endpoints.

**Acceptance Criteria:**
- ✅ OpenAPI schema regenerated
- ✅ Frontend client includes EVM indices service
- ✅ TypeScript types generated correctly
- ✅ No compilation errors

**Test-First Requirement:**
- None (tooling, verified by compilation)

**Files to Modify:**
- Frontend client (auto-generated)

**Dependencies:**
- Phase 4 complete

**Estimated Time:** 15 minutes

---

## TEST COVERAGE SUMMARY

### Service Layer Tests (Phase 1)
- ✅ CPI calculation: normal, undefined cases, quantization, negative values
- ✅ SPI calculation: normal, null cases, quantization, negative values
- ✅ TCPI calculation: normal, overrun cases, undefined cases, quantization, negative values
- ✅ Aggregation: multiple elements, empty, single element, quantization

**Target:** 15-20 service tests passing

### API Layer Tests (Phase 3)
- ✅ WBE endpoint: normal, edge cases, 404, time-machine
- ✅ Project endpoint: normal, edge cases, 404, time-machine, multiple WBEs
- ✅ Helper functions: aggregation, control date filtering

**Target:** 15-20 API tests passing

### Integration Tests (Phase 5)
- ✅ End-to-end scenarios with realistic data
- ✅ Time-machine integration
- ✅ Edge case combinations

**Target:** 4-6 integration tests passing

**Total Test Target:** 34-46 tests passing

---

## ESTIMATED EFFORT

| Phase | Steps | Estimated Time |
|-------|-------|----------------|
| Phase 1: Service Layer | 5 steps | 5-8 hours |
| Phase 2: Response Models | 1 step | 30 minutes |
| Phase 3: API Routes | 4 steps | 7-12 hours |
| Phase 4: Router Registration | 1 step | 15 minutes |
| Phase 5: Integration Testing | 2 steps | 2-3 hours |
| **Total** | **13 steps** | **15-24 hours** |

---

## DEPENDENCIES

- ✅ E4-001 (Planned Value Calculation Engine) - Complete
- ✅ E4-002 (Earned Value Calculation Engine) - Complete
- ✅ E3-002 (Cost Aggregation Logic) - Complete (for AC)
- ✅ PLA-1 (Time-Machine Control Date Filtering) - Complete

**No blocking dependencies** - All prerequisites are complete.

---

## RISKS AND MITIGATION

| Risk | Impact | Mitigation |
|------|--------|------------|
| Inconsistent PV/EV/AC/BAC sources | High | Reuse existing service/endpoint patterns; ensure single source of truth |
| Edge case handling complexity | Medium | Comprehensive test coverage; explicit business rule documentation |
| Performance with large projects | Low | Aggregation patterns already proven in PV/EV; monitor query performance |
| Type system complexity (TCPI 'overrun') | Low | Use Union types; clear documentation in response models |

---

## NEXT STEPS

1. ✅ **Analysis Complete** - High-level analysis documented
2. ✅ **Business Rules Clarified** - Edge cases confirmed
3. ✅ **Detailed Plan Complete** - Ready for implementation
4. **Begin Phase 1** - Start with Step 1.1 (Service Module Structure)
5. **Follow TDD Discipline** - Write failing tests first, then implement
6. **Incremental Commits** - Keep commits small (<100 lines, <5 files)

---

**Reference:** This plan follows the E4-001 Planned Value and E4-002 Earned Value implementation patterns, ensuring architectural consistency across EVM calculation features. All business rules from the analysis document (`docs/analysis/e4-003-918273-evm-performance-indices-analysis.md`) are incorporated.
