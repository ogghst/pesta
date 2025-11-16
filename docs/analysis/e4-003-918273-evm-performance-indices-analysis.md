# High-Level Analysis: E4-003 EVM Performance Indices (CPI, SPI, TCPI)

**Task:** E4-003 - EVM Performance Indices
**Sprint:** Sprint 4 - Earned Value Recording and Core EVM Calculations
**Status:** Analysis Phase
**Date:** 2025-11-16
**Current Time:** 19:22 CET (Europe/Rome)

---

## User Story

As a project manager monitoring performance at a given control date,
I want CPI, SPI, and TCPI metrics at project, WBE, and cost element levels,
So that I can quickly understand whether we are ahead/behind schedule and under/over budget, and what efficiency is required to recover.

---

## 1. CODEBASE PATTERN ANALYSIS

1. **Planned Value (PV) Calculation Engine – E4-001**
   - **Location:** `backend/app/services/planned_value.py`, `backend/app/api/routes/planned_value.py`, related tests under `backend/tests/services/test_planned_value.py` and `backend/tests/api/routes/test_planned_value.py`.
   - **Architecture Layers:**
     - Service layer: pure functions such as `calculate_planned_percent_complete`, `calculate_planned_value`, and aggregation helpers; they use `Decimal`, quantization helpers, and no direct DB access.
     - API layer: FastAPI router that injects `SessionDep`, `CurrentUser`, and time-machine control date, performs queries, selects appropriate schedules, and calls service helpers.
     - Models: PV response schemas in `backend/app/models/...` following the Base/Create/Update/Public pattern.
   - **Patterns to respect:**
     - Strict separation between pure calculation logic and IO (DB/HTTP).
     - Hierarchical aggregation (cost element → WBE → project) implemented in the service layer, with routers wiring up queries.
     - Use of time-machine control date for all PV queries.

2. **Earned Value (EV) Calculation Engine – E4-002**
   - **Location:** `backend/app/services/earned_value.py`, `backend/app/api/routes/earned_value.py`, tests under `backend/tests/services/test_earned_value.py` and `backend/tests/api/routes/test_earned_value.py` (per E4-002 implementation and analysis).
   - **Architecture Layers:**
     - Service layer: `calculate_earned_percent_complete`, `calculate_earned_value`, `calculate_cost_element_earned_value`, and aggregation helpers mirroring PV patterns.
     - API layer: earned value router that resolves control date via the time-machine dependency, selects the most recent earned value entry per cost element (where completion_date ≤ control_date), and aggregates up the hierarchy.
   - **Patterns to respect:**
     - Mirrored structure with PV for consistency.
     - Reuse of time-machine helpers and selection logic.
     - `Decimal`-based math with quantization for financial correctness.

3. **Cost Aggregation and Summary Patterns – E3-002, E2-006**
   - **Location:** `backend/app/api/routes/cost_summary.py` and related services/models; `BudgetSummary` backend/ frontend as documented in `docs/analysis/e3-002-cost-aggregation-logic-analysis.md` and `docs/plans/e2-006-budget-summary-views.plan.md`.
   - **Architecture Layers:**
     - Aggregation endpoints that roll up raw cost registrations into totals and computed ratios (e.g., `cost_percentage_of_budget`).
     - Response schemas that expose both primitive totals and derived metrics.
   - **Relevance:** EVM indices are additional derived metrics based on PV, EV, AC, and BAC; cost summary patterns show how to expose derived ratios cleanly in response models without leaking implementation details.

4. **Time-Machine and Control-Date Patterns – PLA-1 and E4-011**
   - **Location:** Time-machine helpers and routes (e.g., `backend/app/api/routes/budget_timeline.py`, `planned_value.py`, `earned_value.py`), documented in `docs/analysis/PLA_1_high_level_analysis.md` and `docs/analysis/e4-011-time-machine-analysis.md`.
   - **Patterns to respect:**
     - All EVM metrics are computed “as-of” a control date, with both entity `created_at` and effective dates enforced.
     - Shared helper abstractions for end-of-day handling and schedule/entry selection.

### Architectural Layers to Respect

- **Service layer (`backend/app/services/…`)** for pure EVM index calculations (CPI, SPI, TCPI) and hierarchical aggregation.
- **API layer (`backend/app/api/routes/…`)** for wiring control date, querying PV/EV/AC/BAC inputs, and returning EVM index DTOs.
- **Models layer (`backend/app/models/…`)** for typed response schemas that keep index formulas and decimals consistent.
- **Frontend consumption** through existing summary/timeline components, which already expect server-side enforcement of time-machine semantics.

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### Backend Modules and Methods

- **PV/EV Services**
  - `backend/app/services/planned_value.py`: Provides PV values and BAC context per level.
  - `backend/app/services/earned_value.py`: Provides EV values and BAC context per level.
  - **Impact:** EVM index service will either call these helpers directly or rely on their aggregation patterns when computing CPI and SPI.

- **Cost and Budget Aggregations**
  - `backend/app/api/routes/cost_summary.py` (and related services): Expose AC and BAC-like totals.
  - Budget and revenue summaries from E2-006 provide patterns for aggregating totals at WBE/project levels.
  - **Impact:** CPI requires AC, and TCPI requires BAC and AC; these inputs likely come from cost summary logic or shared helpers extracted from it.

- **Time-Machine Control Date**
  - `get_time_machine_control_date` dependency and helpers described in PLA-1/E4-011 analyses.
  - **Impact:** All EVM indices must be computed “as-of” the same control date as PV, EV, and AC to avoid inconsistent ratios.

- **New Service Module (Proposed)**
  - **Candidate:** `backend/app/services/evm_indices.py`
    - Functions like:
      - `calculate_cpi(ev: Decimal, ac: Decimal) -> Decimal | None` (returns None when AC = 0 and EV > 0)
      - `calculate_spi(ev: Decimal, pv: Decimal) -> Decimal | None` (returns None when PV = 0)
      - `calculate_tcpi(bac: Decimal, ev: Decimal, ac: Decimal) -> Decimal | Literal['overrun'] | None` (returns 'overrun' when BAC ≤ AC)
      - Aggregation helpers mirroring PV/EV patterns and handling zero/negative denominators per business rules.

- **New API Router (Proposed)**
  - **Candidate:** `backend/app/api/routes/evm_indices.py`
    - Endpoints (per control date):
      - `GET /projects/{project_id}/evm-indices/cost-elements/{cost_element_id}` (optional in MVP)
      - `GET /projects/{project_id}/evm-indices/wbes/{wbe_id}` (required)
      - `GET /projects/{project_id}/evm-indices` (required)
    - **Dependencies:** `SessionDep`, `CurrentUser`, `get_time_machine_control_date`.
    - **Responsibility:** Query PV/EV/AC/BAC inputs via shared helpers and return CPI/SPI/TCPI indices and raw values for transparency. Indices required at project and WBE levels.

### System Dependencies and External Integrations

- **Database:** Existing PostgreSQL schema already stores:
  - Baseline budgets (BAC), time-phased PV, cost registrations (AC), and earned value entries (EV source).
  - No schema changes are strictly required for index calculation; indices can be computed on the fly.
- **Frontend:** Existing components (e.g., `BudgetSummary`, `CostSummary`, `BudgetTimeline`, Earned Value summaries) will eventually consume EVM indices.
  - For E4-003, backend APIs and tests are the primary scope; UI consumption can be staged later (likely E4-006).
- **Analytics Libraries (Context7 Insight):**
  - Context7’s pandas documentation for time series and financial calculations confirms that ratio-based performance metrics are typically computed over aggregated time windows using standard arithmetic (e.g., resampling and aggregations).
  - Given the simplicity of CPI/SPI/TCPI formulas and the existing `Decimal` patterns, no external numeric library is required for the core indices; pandas (or similar) remains more relevant to downstream reporting/export tasks, not the core engine.

### Configuration Patterns

- Reuse existing configuration for:
  - Time-machine control date persistence and injection.
  - Decimal precision (two or four decimal places) used consistently across PV, EV, AC, and budgets.
  - API versioning and path conventions under `/api/v1/projects/{project_id}/…`.

---

## 3. ABSTRACTION INVENTORY

- **Decimal Quantization Helpers**
  - PV and EV services define `TWO_PLACES`, `FOUR_PLACES`, `_quantize`, and use `ROUND_HALF_UP` for financial rounding.
  - EVM indices should reuse these helpers or a shared financial math utility to avoid divergent rounding behavior.

- **Aggregation Patterns**
  - PV/EV services and cost summary endpoints already implement aggregation patterns that:
    - Sum values and BAC across cost elements.
    - Compute weighted percentages or ratios at higher levels.
  - EVM indices can lean on these aggregated totals rather than re-implementing traversal logic.

- **Time-Machine Helpers**
  - Shared control-date logic (e.g., `_end_of_day`, schedule/entry selection helpers, `get_time_machine_control_date`) enforces historical correctness across PV, EV, and cost timelines.
  - Indices must be computed using values that already respect these filters.

- **Testing Utilities**
  - Existing pytest fixtures for projects, WBEs, cost elements, schedules, cost registrations, and earned value entries.
  - Helpers such as `set_time_machine_date` (per PLA-1 analysis) and baseline creation utilities.
  - E4-003 tests can reuse these fixtures to construct scenarios where PV/EV/AC/BAC relationships produce known CPI/SPI/TCPI values.

- **Frontend Patterns (For Later Reuse)**
  - `BudgetSummary` and `CostSummary` components already display ratios and colored status indicators.
  - Once indices exist, these components (or new EVM summary components) can reuse the same visual patterns for thresholds (e.g., CPI < 1 red, ≈1 amber, >1 green).

---

## 4. ALTERNATIVE APPROACHES

### Approach A – Dedicated EVM Indices Service + Router (Recommended)

- **Summary:** Create `evm_indices` service and API router that compute CPI, SPI, and TCPI by combining PV, EV, AC, and BAC inputs as-of the control date, following the PV/EV architectural patterns.
- **Formulas (from PRD/standard EVM):**
  - \(CPI = \frac{EV}{AC}\) (undefined when AC = 0 and EV > 0)
  - \(SPI = \frac{EV}{PV}\) (null when PV = 0)
  - \(TCPI = \frac{BAC - EV}{BAC - AC}\) (returns 'overrun' when BAC ≤ AC; otherwise computed value)
- **Pros:**
  - Clear separation of concerns; PV/EV/AC remain standalone, indices live in a focused module.
  - Easy to test and reason about with pure functions.
  - Aligns with existing E4-001/E4-002 patterns and time-machine infrastructure.
- **Cons/Risks:**
  - Introduces another API surface area to document and maintain.
  - Requires careful handling of edge cases (division by zero, missing PV/EV/AC/BAC).
- **Architectural Alignment:** High – mirrors existing service/router split and respects TDD discipline.
- **Estimated Complexity:** Medium – arithmetic is simple, but wiring and test coverage across three hierarchy levels add surface area.
- **Risk Factors:**
  - Misaligned control dates or inconsistent aggregation sources could yield misleading indices.
  - Business rules clarified: CPI undefined when AC = 0 and EV > 0; SPI null when PV = 0; TCPI returns 'overrun' when BAC ≤ AC.

### Approach B – Extend Existing PV/EV/Cost Summary Endpoints to Include Indices

- **Summary:** Add CPI/SPI/TCPI fields directly to existing PV, EV, or cost summary responses by computing indices within those routers or shared helpers.
- **Pros:**
  - Fewer endpoints for clients to call; simpler for consumers.
  - Reuses existing query paths and DTOs.
- **Cons/Risks:**
  - Blurs responsibilities of PV/EV endpoints (they become “multi-purpose”).
  - Tight coupling between calculations makes future refactors harder (e.g., changing PV without impacting indices).
  - Larger DTOs and more complex tests per endpoint.
- **Architectural Alignment:** Medium – still server-side, but less clean separation than a dedicated indices module.
- **Estimated Complexity:** Medium – similar logic but more refactoring risk.
- **Risk Factors:**
  - Higher chance of regression in currently stable PV/EV endpoints.
  - Potential for circular dependencies if not carefully structured.

### Approach C – Client-Side Index Calculation Using Existing APIs

- **Summary:** Keep backend limited to PV, EV, AC, and BAC endpoints; compute CPI/SPI/TCPI entirely in the frontend or external analytics tools.
- **Pros:**
  - Zero backend changes; reuses existing APIs.
  - Allows flexible experimentation with additional derived metrics in the UI.
- **Cons/Risks:**
  - Violates single-source-of-truth principle for EVM calculations.
  - Harder to test and validate; multiple clients may implement formulas differently.
  - Time-machine consistency harder to guarantee if clients mix data from different control dates.
- **Architectural Alignment:** Low – shifts core EVM logic out of the backend where other calculations live.
- **Estimated Complexity:** Low for initial implementation, but higher long-term maintenance burden.
- **Risk Factors:**
  - Inconsistent metrics across consumers.
  - More difficult to support reporting/export or external integrations expecting server-side indices.

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

- **Principles Followed (for Approach A):**
  - **Single Source of Truth:** All core EVM math (PV, EV, AC, BAC, CPI, SPI, TCPI) resides in backend services with tests.
  - **Separation of Concerns:** Dedicated service/router for indices; PV, EV, and cost aggregation remain focused.
  - **Time-Machine Consistency:** Indices rely on values computed as-of a single control date, respecting PLA-1/E4-011 semantics.
  - **Reusability:** Shared helpers and quantization utilities reduce duplication.

- **Potential Maintenance Burden:**
  - Additional service/router introduces new tests and docs to keep in sync.
  - Any change to PV, EV, or AC definitions must consider downstream impact on indices (and vice versa).
  - If indices are later needed in multiple contexts (dashboards, reports, exports), we must maintain API versioning and backwards compatibility.

- **Testing Challenges:**
  - Need scenario matrices covering:
    - Normal cases (EV, PV, AC > 0, BAC > 0) with expected CPI/SPI/TCPI.
    - Edge cases per business rules:
      - CPI: AC = 0 and EV > 0 → undefined (None)
      - SPI: PV = 0 → null (None)
      - TCPI: BAC ≤ AC → 'overrun' (string literal)
    - Additional edge cases: BAC = 0, EV = 0, combinations near boundaries.
    - Time-machine scenarios where values change as control date moves (e.g., before costs posted, after costs posted).
  - Business rules now clarified; tests must assert explicit behavior for each edge case.
  - Hierarchical tests for WBE and project levels (required) to verify aggregation and weighting are correct.

---

## Risks, Unknowns, and Ambiguities

- **Business Rules Clarified (2025-11-16):**
  - ✅ **CPI behavior:** CPI shall be undefined (None) when AC = 0 and EV > 0.
  - ✅ **SPI behavior:** SPI shall be null (None) when PV = 0.
  - ✅ **TCPI behavior:** TCPI shall return 'overrun' (string literal) when BAC ≤ AC.
  - ✅ **Required levels:** Indices are required at project and WBE levels (cost element level optional in MVP).

- **Performance Considerations:**
  - EVM indices rely on PV, EV, AC, and BAC; if each is obtained via separate queries, we need to ensure efficient aggregation and avoid N+1 patterns.
  - Depending on volumes, we may need to cache or precompute some aggregates, especially at project level for dashboard use cases.

- **Data Quality Risks:**
  - Incomplete or inconsistent EV or cost registration data can yield misleading indices even if formulas are correct.
  - Need clear documentation and possibly UI indicators when required inputs are missing (e.g., no EV yet → indices not available).

---

## Summary & Next Steps

- **What:** Introduce an EVM Performance Indices engine that computes CPI, SPI, and TCPI as-of a control date at project and WBE levels (cost element optional), using existing PV, EV, AC, and BAC inputs.
- **Why:** Provide project managers with standard EVM health indicators to assess cost and schedule performance and understand the efficiency required to complete remaining work within budget.
- **Recommended Approach:** **Approach A – Dedicated EVM indices service and router**, mirroring existing PV/EV architecture, with pure calculation helpers and a focused API surface.
- **Business Rules Confirmed (2025-11-16):**
  - CPI = undefined when AC = 0 and EV > 0
  - SPI = null when PV = 0
  - TCPI = 'overrun' when BAC ≤ AC
  - Indices required at project and WBE levels
- **Next Steps:** Proceed to detailed planning with a TDD-focused implementation plan and explicit failing tests for the confirmed edge cases above.

---

**Reference:** This analysis follows the PLA-1 high-level analysis template and leverages existing PV/EV, cost summary, and time-machine patterns documented in `docs/analysis/*.md`. Context7's pandas time-series and financial aggregation patterns were reviewed to confirm that simple ratio-based EVM indices can remain in native `Decimal` logic without introducing additional numeric libraries.
