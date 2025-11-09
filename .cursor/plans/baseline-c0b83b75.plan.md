<!-- c0b83b75-c45d-452a-a07f-d0839627687d 59efdcbe-01a9-4a15-8f79-d5999a81b427 -->
# Earned Value Baseline Decoupling Plan

## Goals

- Remove any baseline linkage from `EarnedValueEntry`
- Persist `percent_complete` snapshots on `BaselineCostElement`
- Refresh API, client, UI, and docs to match the new data model

## Implementation Steps

1. **Guard Tests for New Behaviour** (`backend/tests/api/routes/test_earned_value_entries.py`, `backend/tests/models/test_earned_value_entry.py`, `backend/tests/api/routes/test_baseline_logs.py`)

- Add failing assertions that `baseline_id` is no longer exposed/required for earned value entries and that baseline snapshots capture `percent_complete` from the latest entry.

2. **Schema & Migration Updates** (`backend/app/models/earned_value_entry.py`, `backend/app/models/baseline_cost_element.py`, new Alembic migration)

- Remove `baseline_id` field/relationship from `EarnedValueEntry` and add `percent_complete` column to `BaselineCostElement`, adjusting Pydantic schemas accordingly.

3. **Service Logic Adjustments** (`backend/app/api/routes/earned_value_entries.py`, `backend/app/api/routes/baseline_logs.py`, associated utils/tests)

- Drop auto-baseline association logic, update snapshot creation to store both `earned_ev` and `percent_complete`, and align validation/workflow plus unit tests.

4. **Client & Frontend Refresh** (`frontend/src/client`, `frontend/src/components/Projects/earnedValueColumns.tsx`, related views/tests)

- Regenerate OpenAPI client, remove baseline column/logic from earned value tables/forms, and surface new snapshot percent data where relevant; update Vitest/e2e specs.

5. **Documentation Alignment** (`docs/data_model.md`, `docs/prd.md`, `docs/plan.md`, `docs/project_status.md`)

- Revise narratives and diagrams to reflect the decoupled earned value entries and new percent snapshot field, including status summaries.

## Tracking

- Maintain TDD: ensure each feature change starts from the failing tests created in Step 1.
- Keep migrations <100 lines and commits atomic to satisfy working agreements.
- Re-run test suites touching earned value and baseline flows before concluding.
