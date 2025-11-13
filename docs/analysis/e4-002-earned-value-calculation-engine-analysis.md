# High-Level Analysis: E4-002 Earned Value Calculation Engine

**Task:** E4-002 - Earned Value Calculation Engine
**Sprint:** Sprint 4 - Earned Value Recording and Core EVM Calculations
**Status:** Analysis Phase
**Date:** 2025-11-13

---

## Objective

Compute Earned Value (EV) = BAC × physical completion % from earned value entries at cost element, WBE, and project levels. This is the core EVM metric alongside Planned Value (PV) from E4-001 and will feed into E4-003 (Performance Indices) and E4-004 (Variance Calculations).

---

## User Story

**As a** project manager
**I want** to calculate Earned Value (EV) for cost elements, WBEs, and projects at any control date
**So that** I can assess physical progress against budget and compare with Planned Value for performance analysis

---

## Requirements Summary

**From PRD (Section 6.2 & 12.2):**
- Earned Value (EV) = BAC × physical completion percentage
- Physical completion percentage is based on recorded earned value entries
- EV must be calculated at cost element, WBE, and project levels
- EV calculation requires a control date parameter

**From Plan.md (Sprint 4):**
- Implement earned value calculation engine
- Support hierarchical aggregation (cost element → WBE → project)
- Core EVM metric required before performance indices (CPI, SPI) and variances (CV, SV)

**From Project Status:**
- E3-006 (Earned Value Recording Interface) is complete - earned value entries can be created/updated/deleted
- E4-001 (Planned Value Calculation Engine) is complete - provides architectural pattern to follow
- E4-002 is required before E4-003 (Performance Indices) and E4-004 (Variance Calculations)

**Key Difference from PV:**
- **Planned Value (PV)**: Uses schedule baseline (time-based progression) - what *should* be done
- **Earned Value (EV)**: Uses earned value entries (recorded completion %) - what *has been* done
- Both use the same formula: `BAC × percent_complete`, but source of percent differs

---

## 1. CODEBASE PATTERN ANALYSIS

### Existing Pattern 1: Planned Value Calculation Engine (E4-001)

**Location:** `backend/app/services/planned_value.py`, `backend/app/api/routes/planned_value.py`

**Architecture Layers:**
- **Service Layer:** Pure calculation functions (no database access)
  - `calculate_planned_percent_complete()` - progression math
  - `calculate_planned_value()` - BAC × percent
  - `calculate_cost_element_planned_value()` - cost element wrapper
  - `aggregate_planned_value()` - roll-up aggregation
- **API Layer:** FastAPI routes with database queries
  - `GET /projects/{project_id}/planned-value/cost-elements/{cost_element_id}`
  - `GET /projects/{project_id}/planned-value/wbes/{wbe_id}`
  - `GET /projects/{project_id}/planned-value`
- **Models Layer:** Response schemas (`PlannedValueBase`, `PlannedValueCostElementPublic`, etc.)

**Key Patterns:**
- Service functions are pure (no session dependencies)
- API routes handle database queries and entity validation
- Control date selection logic in API layer (`_select_schedule_for_cost_element`)
- Aggregation uses tuples `(value, bac)` pattern
- Error handling via custom exception (`PlannedValueError`)

**Test Structure:**
- Service tests: Unit tests for calculation logic (progression types, edge cases)
- API tests: Integration tests with database fixtures (cost element/WBE/project levels)

### Existing Pattern 2: Cost Aggregation (E3-002)

**Location:** `backend/app/api/routes/cost_summary.py`

**Pattern:**
- Hierarchical aggregation (cost element → WBE → project)
- Uses SQLModel queries with Python sum aggregation
- Response models with computed fields (`cost_percentage_of_budget`)
- Multiple endpoints following consistent structure

**Relevance:** Similar aggregation pattern, but for cost data instead of EV calculations.

### Existing Pattern 3: Earned Value Entry CRUD (E3-006)

**Location:** `backend/app/api/routes/earned_value_entries.py`

**Key Findings:**
- Simple `calculate_earned_value()` function already exists (lines 134-143)
  - Formula: `BAC × (percent_complete / 100)`
  - Used during entry creation/update
- Earned value entries have `completion_date` field (used as control date proxy)
- Entries are unique per cost element per completion date
- Current implementation calculates EV for individual entries, not aggregated levels

**Gap:** No service layer for EV calculation at control dates with aggregation across levels.

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### Backend Touchpoints

**New Files to Create:**
1. `backend/app/services/earned_value.py`
   - `calculate_earned_percent_complete()` - get percent from most recent entry ≤ control_date
   - `calculate_earned_value()` - EV = BAC × percent (may enhance existing)
   - `calculate_cost_element_earned_value()` - cost element wrapper
   - `aggregate_earned_value()` - roll-up aggregation (mirror `aggregate_planned_value`)

2. `backend/app/api/routes/earned_value.py`
   - Three endpoints mirroring planned_value routes:
     - `GET /projects/{project_id}/earned-value/cost-elements/{cost_element_id}`
     - `GET /projects/{project_id}/earned-value/wbes/{wbe_id}`
     - `GET /projects/{project_id}/earned-value`

3. `backend/app/models/earned_value.py`
   - Response schemas mirroring planned_value models:
     - `EarnedValueBase`
     - `EarnedValueCostElementPublic`
     - `EarnedValueWBEPublic`
     - `EarnedValueProjectPublic`

4. Test files:
   - `backend/tests/services/test_earned_value.py`
   - `backend/tests/api/routes/test_earned_value.py`

**Files to Modify:**
1. `backend/app/api/main.py`
   - Add `earned_value` router import and registration

2. `backend/app/models/__init__.py`
   - Export new earned value response models

### Frontend Touchpoints (Future - Not in E4-002 scope)

- Will need UI components to display EV metrics (likely in Sprint 5)
- Budget Timeline component already displays EV in charts (`frontend/src/components/Projects/BudgetTimeline.tsx`)

### Database Touchpoints

**No schema changes required:**
- `EarnedValueEntry` model already supports the required fields
- Query pattern: Select most recent entry per cost element where `completion_date ≤ control_date`

---

## 3. ABSTRACTION INVENTORY

### Reusable Abstractions

**From Planned Value (E4-001):**
1. **Service Pattern:** Pure calculation functions with Decimal precision
   - `_quantize()` helper for rounding
   - Constants: `TWO_PLACES`, `FOUR_PLACES`, `ZERO`, `ONE`
   - `AggregateResult` dataclass pattern

2. **API Pattern:** Route structure with helper functions
   - `_ensure_project_exists()` validation
   - `_select_*_for_cost_element()` query helpers
   - `_get_*_map()` batch query optimization
   - `_quantize_decimal()` response formatting

3. **Response Model Pattern:** Base schema with level-specific extensions
   - `*Base` schema with common fields
   - `*CostElementPublic`, `*WBEPublic`, `*ProjectPublic` extensions

**Existing Utilities:**
- `calculate_earned_value()` in `earned_value_entries.py` - can be moved/refactored to service layer
- Test fixtures from `tests/utils/earned_value_entry.py`

### Patterns to Follow

1. **Decimal Precision:**
   - EV values: 2 decimal places (`TWO_PLACES`)
   - Percent complete: 4 decimal places (`FOUR_PLACES`)
   - Consistent with PV implementation

2. **Control Date Logic:**
   - Select most recent earned value entry where `completion_date ≤ control_date`
   - If no entry exists, return 0% complete (similar to PV with no schedule)
   - Per cost element, then aggregate up hierarchy

3. **Aggregation Logic:**
   - Sum EV values across cost elements
   - Sum BAC values across cost elements
   - Calculate weighted percent complete = total_EV / total_BAC
   - Mirror `aggregate_planned_value()` structure

---

## 4. ALTERNATIVE APPROACHES

### Approach 1: Mirror Planned Value Architecture (RECOMMENDED)

**Description:** Create parallel service/API/model structure following E4-001 patterns exactly.

**Pros:**
- ✅ Consistent architecture with PV implementation
- ✅ Easy to understand and maintain
- ✅ Leverages proven patterns from E4-001
- ✅ Minimal learning curve for developers
- ✅ Clear separation of concerns (service vs API layers)

**Cons:**
- ⚠️ Some code duplication between PV and EV services (acceptable trade-off)
- ⚠️ Three separate endpoints instead of unified EVM endpoint

**Estimated Complexity:** Low (follow established patterns)

**Alignment:** 100% aligned with existing architecture

**Risk Factors:**
- Low risk - proven pattern from E4-001
- Risk: Control date selection logic slightly different (completion_date vs registration_date)

### Approach 2: Unified EVM Calculation Service

**Description:** Single service/API layer that calculates both PV and EV together, returning combined metrics.

**Pros:**
- ✅ Single endpoint reduces API calls
- ✅ Guarantees PV and EV use same control date
- ✅ Better performance (one query instead of two)

**Cons:**
- ❌ Mixes concerns (PV uses schedules, EV uses entries)
- ❌ Violates single responsibility principle
- ❌ More complex API response models
- ❌ Less flexible (can't query PV or EV independently)

**Estimated Complexity:** Medium-High (requires refactoring PV code)

**Alignment:** Diverges from established patterns

**Risk Factors:**
- Medium risk - requires changes to existing PV code
- Risk: Breaking changes to existing PV API consumers

### Approach 3: Extend Existing Earned Value Entry Routes

**Description:** Add aggregation endpoints directly to `earned_value_entries.py` router.

**Pros:**
- ✅ No new router to manage
- ✅ Colocated with EV entry CRUD operations

**Cons:**
- ❌ Mixes CRUD operations with calculation endpoints
- ❌ Inconsistent with PV pattern (PV has separate router)
- ❌ Larger file, harder to maintain
- ❌ Service layer would still be needed, just organized differently

**Estimated Complexity:** Low-Medium

**Alignment:** Partially aligned (same router, but different organizational pattern)

**Risk Factors:**
- Low risk, but creates inconsistency

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### Architectural Principles

**Follows:**
- ✅ **Separation of Concerns:** Service layer (calculations) separate from API layer (queries/validation)
- ✅ **Single Responsibility:** Each function has one clear purpose
- ✅ **DRY (Don't Repeat Yourself):** Reuses patterns from E4-001
- ✅ **Open/Closed Principle:** Extends functionality without modifying existing PV code
- ✅ **Consistency:** Mirrors established PV architecture

**Potential Violations:**
- ⚠️ **DRY:** Some code duplication between PV and EV services (acceptable - they are conceptually different)
- ⚠️ **YAGNI:** Creating three endpoints when one unified might work (but flexibility is valuable)

### Maintenance Burden

**Low Risk Areas:**
- Service layer is pure functions (easy to test, no side effects)
- API routes follow proven patterns
- Clear separation makes changes localized

**Potential Future Issues:**
1. **Code Duplication:** PV and EV services have similar structure but different logic
   - *Mitigation:* Shared helpers for aggregation, quantization
   - *Trade-off:* Acceptable duplication for clarity

2. **Control Date Logic:** Different selection logic for PV (schedule registration_date) vs EV (completion_date)
   - *Mitigation:* Clear documentation, separate helper functions
   - *Note:* This is intentional - they use different data sources

3. **Response Model Duplication:** Similar schemas for PV and EV responses
   - *Mitigation:* Could create shared base if needed in future
   - *Current:* Acceptable duplication for type safety

### Testing Challenges

**Unit Tests (Service Layer):**
- ✅ Straightforward - pure functions with Decimal inputs/outputs
- ✅ Can test edge cases: no entries, entries before/after control date, zero BAC
- ✅ Mock-free (pure functions)

**Integration Tests (API Layer):**
- ✅ Follow established patterns from PV tests
- ✅ Test fixture helpers already exist (`create_earned_value_entry`)
- ⚠️ Challenge: Ensuring correct entry selection at control date (multiple entries per cost element)
- ⚠️ Challenge: Testing aggregation across multiple cost elements/WBEs

**Edge Cases to Test:**
1. Cost element with no earned value entries → 0% complete
2. Control date before any entries → 0% complete
3. Control date after latest entry → use latest entry
4. Multiple entries for same cost element → select most recent ≤ control_date
5. Empty projects/WBEs → 0 EV, 0 BAC
6. Cost elements with BAC = 0 → handle division by zero in aggregation

---

## 6. RISKS AND UNKNOWNS

### Technical Risks

1. **Entry Selection Logic:**
   - **Risk:** How to handle multiple entries per cost element at control date?
   - **Mitigation:** Select most recent entry where `completion_date ≤ control_date` (standard EVM practice)
   - **Clarification Needed:** Is this the correct business rule?

2. **Percent Complete Accumulation:**
   - **Risk:** EV entries can have percent_complete > 100% or decreasing values (corrections)?
   - **Current Understanding:** Each entry is a snapshot - use the most recent value
   - **Mitigation:** Validation already exists (0-100 range), but corrections may decrease percent
   - **Clarification Needed:** Should we track cumulative or absolute percent?

3. **Baseline Integration:**
   - **Unknown:** E3-007 (Earned Value Baseline Management) is not yet implemented
   - **Impact:** May need to support baseline EV calculations in future
   - **Mitigation:** Keep service layer flexible, API can add baseline filtering later

### Business Logic Risks

1. **Control Date Semantics:**
   - **Question:** If control_date is exactly a completion_date, include or exclude?
   - **Recommendation:** Include (use `<=` comparison) - standard EVM practice

2. **Aggregation Weighting:**
   - **Question:** Should EV percent at project level be weighted by BAC or simple average?
   - **Recommendation:** Weighted by BAC (EV / BAC) - consistent with PV implementation

3. **Missing Entries:**
   - **Question:** How to handle cost elements without any earned value entries?
   - **Recommendation:** Return 0% complete, 0 EV - consistent with PV (no schedule = 0 PV)

### Performance Considerations

1. **Query Optimization:**
   - **Risk:** Selecting latest entry per cost element could be slow with many entries
   - **Mitigation:** Use efficient SQL with window functions or subqueries
   - **Future:** Add database indexes if needed (`(cost_element_id, completion_date DESC)`)

2. **Aggregation Performance:**
   - **Risk:** Aggregating across many cost elements/WBEs
   - **Mitigation:** Similar to PV - proven pattern, should scale
   - **Future:** Consider caching for frequently accessed control dates

---

## 7. QUESTIONS FOR STAKEHOLDER CLARIFICATION

1. **Entry Selection:** Confirm that we should use the most recent earned value entry where `completion_date ≤ control_date` for each cost element.

2. **Percent Complete:** If an earned value entry has percent_complete = 50%, then a later entry has 30% (correction), should we use 30% at that control date? (Assuming yes - each entry is a snapshot)

3. **Baseline Integration:** Should E4-002 support baseline filtering, or is that deferred to E3-007 implementation?

4. **Zero EV Handling:** For cost elements with no earned value entries, return 0% complete (consistent with PV), correct?

5. **Frontend Integration:** Is EV calculation API needed for Sprint 4, or can frontend integration wait until Sprint 5?

---

## 8. RECOMMENDATION

**Recommended Approach: Approach 1 - Mirror Planned Value Architecture**

**Rationale:**
1. **Proven Pattern:** E4-001 is complete and tested - following same pattern reduces risk
2. **Consistency:** Maintains architectural consistency across EVM calculation features
3. **Maintainability:** Clear separation of concerns, easy to understand and modify
4. **Flexibility:** Allows independent querying of EV (useful for debugging, reporting)
5. **Low Complexity:** Can leverage existing patterns, reducing implementation time

**Implementation Strategy:**
1. Create `backend/app/services/earned_value.py` following `planned_value.py` structure
2. Create `backend/app/api/routes/earned_value.py` with three endpoints (cost element, WBE, project)
3. Create `backend/app/models/earned_value.py` with response schemas
4. Write comprehensive tests following PV test patterns
5. Register router in `main.py`

**Estimated Effort:**
- Backend service layer: 4-6 hours
- API routes and models: 4-6 hours
- Tests (service + API): 4-6 hours
- **Total: 12-18 hours**

**Dependencies:**
- ✅ E3-006 (Earned Value Recording) - Complete
- ✅ E4-001 (Planned Value) - Complete (pattern reference)
- ⏳ No blocking dependencies

**Next Steps:**
1. Get stakeholder confirmation on business rules (entry selection, percent handling)
2. Proceed to detailed planning phase with TDD approach
3. Implement service layer first (pure functions, easy to test)
4. Then API layer (integration tests)
5. Finally, integrate into main router

---

## 9. SUMMARY

**Feature:** Earned Value Calculation Engine computing EV = BAC × physical completion % at cost element, WBE, and project levels using earned value entries.

**Architecture:** Mirror E4-001 Planned Value pattern with separate service, API, and model layers.

**Key Technical Decision:** Use most recent earned value entry where `completion_date ≤ control_date` for each cost element, then aggregate up hierarchy.

**Risk Level:** Low - following proven patterns, but requires clarification on entry selection business rules.

**Estimated Effort:** 12-18 hours (backend only, frontend deferred to Sprint 5).

---

**Document Owner:** Development Team
**Review Status:** Pending stakeholder feedback on business rule questions
**Next Phase:** Detailed TDD planning after clarification received
