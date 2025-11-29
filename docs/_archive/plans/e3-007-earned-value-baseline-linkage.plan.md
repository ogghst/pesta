# E3-007 Earned Value Baseline Linkage – High-Level Analysis

**Prepared:** 2025-11-08 08:13 CET
**Author:** GPT-5 Codex (assistant)
**Status:** Analysis Complete – pending detailed planning & TDD step breakdown

---

## 1. Objective & Scope

Implement `E3-007` by linking earned value entries to baseline logs so that historical earned value (EV) data aligns with the immutable baseline snapshots used elsewhere in the system. Work must respect existing FastAPI/SQLModel architecture, maintain TDD discipline, and stay within incremental-change bounds (<100 LOC / ≤5 files per commit).

---

## 2. Codebase Pattern Inventory

- **Baseline Snapshot Helper (`backend/app/api/routes/baseline_logs.py#create_baseline_cost_elements_for_baseline_log`)**
  Demonstrates how baseline log creation auto-snapshots operational records (cost elements, costs, forecasts, earned value) into baseline-scoped tables. Pattern: router → helper → SQLModel write.

- **Earned Value Entry Router (`backend/app/api/routes/earned_value_entries.py`)**
  Provides CRUD + validation hooks for EV entries. Illustrates use of SQLModel schemas, schedule validation, BAC-based EV derivation, and JSON responses with optional warnings.

- **Schedule/Baseline-ready Models (`backend/app/models/cost_element_schedule.py`, `backend/app/models/earned_value_entry.py`)**
  Both already expose optional `baseline_id` fields, confirming architectural intent to associate operational records with baselines without duplicating schema logic elsewhere.

Architectural layers: FastAPI routers, helper/service functions, SQLModel ORM, Test suite under `backend/tests/api/routes`, and React components under `frontend/src/components/Projects`.

---

## 3. Integration Touchpoints

- **Models:** `EarnedValueEntry` (baseline association + immutability rule), possibly `BaselineLog` if metadata needed.
- **APIs:** `create_earned_value_entry`, `update_earned_value_entry`, new baseline-filtered list route(s).
- **Helpers:** `create_baseline_cost_elements_for_baseline_log` must avoid double-counting once baseline-specific EV is available.
- **Frontend:** `AddEarnedValueEntry` modal, Earned Value tab in `projects.$id.wbes.$wbeId.cost-elements.$costElementId.tsx`, reporting views needing baseline filter.
- **Tests:** `backend/tests/api/routes/test_earned_value_entries.py`, baseline-related suites, Playwright spec for cost element tabs.

Dependencies: existing FastAPI DI (`SessionDep`, `CurrentUser`) and React Query data loaders. No external services.

---

## 4. Abstractions & Reuse

- SQLModel schema pattern (`Base/Create/Update/Public`) ready for extension.
- Validation utilities in EV router for percent/date constraints can host new baseline rules.
- Test utilities (`tests.utils.cost_element`, `tests.utils.earned_value_entry`, baseline fixtures) support TDD setup.
- React modals follow shared form abstractions (React Hook Form, Chakra UI).
- Query filtering patterns already exist (e.g., `cost-elements-with-schedules` endpoint) to emulate for baseline filters.

---

## 5. Clarifications / Ambiguities (Resolved)

- **Baseline selection:** Automatically bind entries to the latest active baseline at creation time.
- **Post-baseline editability:** Once an entry is associated to a baseline, it becomes immutable (updates must be blocked; deletions may require policy confirmation).
- **Baseline reporting:** Introduce filtering endpoints to list/read EV entries by baseline for reporting consumers.

Open questions before implementation:
1. Should deletion also be disallowed for baselined entries, or is soft-delete acceptable?
2. When no baseline exists, do entries remain baseline-neutral (NULL) and editable?
3. How should updates behave when a newer baseline is created after entry creation?

---

## 6. Alternative Approaches (Evaluated)

| Approach | Summary | Pros | Cons / Risks | Complexity | Alignment |
| --- | --- | --- | --- | --- | --- |
| **A. Inline baseline binding** *(Recommended)* | Set `baseline_id` on entries when they are created or when latest baseline is available; enforce immutability. | Minimal schema change, leverages existing optional field, keeps single source of truth. | Needs deterministic baseline resolution + UI feedback; guard against stale baseline pointer. | Medium | High – matches current model design. |
| **B. Snapshot duplicate table** | Copy EV entries into new `BaselineEarnedValueEntry` at baseline creation. | Keeps operational data editable; mirroring snapshot pattern. | Data duplication, new migrations/endpoints, drift risk. | High | Medium – increases maintenance burden. |
| **C. Async/Batch association** | Assign baselines via background job/admin action. | Decouples runtime logic. | Introduces new infrastructure (tasks/cron), delays feedback. | High | Low – outside current architecture. |

Approach A chosen given clarified requirements.

---

## 7. Architectural Impact & Risks

- **Principles upheld:** Reuse of existing SQLModel fields, FastAPI DI, snapshot immutability.
- **Risks:**
  - Baseline resolution race conditions if baseline changes during entry creation.
  - UI must clearly communicate non-editable state for baselined entries.
  - Reporting endpoints need pagination/validation similar to existing list routes.
- **Testing challenges:**
  - Ensure RED phase covers immutability and baseline-filtering behavior.
  - Need fixtures for baseline creation order and verifying latest baseline selection.
  - Frontend tests must validate disabled edit actions for baselined records.

---

## 8. Next Steps

1. Draft detailed TDD implementation plan (steps for failing tests → code updates → refactors).
2. Confirm open questions with stakeholders (see §5).
3. Begin TDD cycle per working agreements once plan approved.

---

## 9. Baseline Reporting Endpoints (In Progress)

- **Goal:** Provide read-only endpoints exposing earned value entries scoped to a given baseline log for reporting/analytics.
- **Patterns to mirror:** Baseline cost element endpoints under `backend/app/api/routes/baseline_logs.py` (`cost-elements-by-wbe`, `cost-elements`).
- **Tentative approach:** Add `GET /projects/{project_id}/baseline-logs/{baseline_id}/earned-value-entries` returning `EarnedValueEntriesPublic` with standard pagination (skip/limit) and optional `cost_element_id` filter.
- **Testing plan:**
  1. RED – API test ensuring baseline-scoped list returns only entries tied to the specified baseline.
  2. RED – API test for missing or cross-project baselines (expect 404).
  3. GREEN – Implement query with join/filters and pagination mirroring existing patterns.
  4. GREEN – Expose optional filtering; ensure count reflects filtered set.
  5. REFACTOR – Share query helpers if duplication emerges between general list and baseline-scoped list.
- **Frontend follow-up (separate task):** update reporting views to use new endpoint.

---
