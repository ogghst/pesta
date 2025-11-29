# PLAN: Frontend Build Recovery (PLA_2_detailed_planning)

## IMPLEMENTATION STEPS

1. **Update test fixtures & unused references**
   - **Description:** Align all frontend test fixtures/mocks with the latest OpenAPI types (add required fields, remove obsolete props, drop unused imports/variables such as `_coNumberField`, `within`). No production code yet.
   - **Acceptance Criteria:** Targeted suites (`pnpm test src/components/Projects/ChangeOrderLineItemsTable.test.tsx src/components/Projects/BranchManagement.test.tsx src/components/Projects/BranchLocking.test.tsx src/components/Projects/CloneBranch.test.tsx src/components/Projects/BranchPermissions.test.tsx src/components/Projects/BranchNaming.test.tsx src/components/Projects/__tests__/ViewBaseline.test.tsx`) run red before changes and green after, with type checking succeeding for the touched tests.
   - **Test-first Requirement:** Execute the above `pnpm test` command and observe the current failures prior to editing any code.
   - **Files Expected:** `frontend/src/components/Projects/*test.tsx`, `frontend/src/components/__tests__/ViewBaseline.test.tsx`.
   - **Dependencies:** None.

2. **Fix dialog & Chakra prop regressions**
   - **Description:** Update all dialog/stack usages to match the new component API (e.g., remove deprecated `size`/`spacing` props or replace with supported equivalents). Cover `MergeBranchDialog.tsx`, `RollbackVersion.tsx`, `BranchMergePreview.tsx`, and any other Chakra wrappers flagged during build.
   - **Acceptance Criteria:** `pnpm test src/components/Projects/MergeBranchDialog.test.tsx src/components/Projects/RollbackVersion.test.tsx src/components/Projects/BranchMergePreview.test.tsx` fails before edits and passes (including type check) afterward.
   - **Test-first Requirement:** Run the targeted tests and confirm they fail/throw prior to modification.
   - **Files Expected:** `frontend/src/components/Projects/MergeBranchDialog.tsx`, `RollbackVersion.tsx`, `BranchMergePreview.tsx` and related tests.
   - **Dependencies:** Step 1 (tests rely on corrected fixtures).

3. **Realign “Add” forms with API contracts**
   - **Description:** Update `AddWBE`, `AddProject`, `AddCostElement`, `AddChangeOrder`, `AddCostElement.tsx` default values, validation schemas, and select components to remove non-existent fields (`status`, `branch`), ensure `Controller` bindings only reference valid API attributes, and adjust RHF generics to use the correct `TFieldValues`.
   - **Acceptance Criteria:** `pnpm test src/components/Projects/AddWBE.tsx src/components/Projects/AddProject.tsx src/components/Projects/AddCostElement.tsx src/components/Projects/AddChangeOrder.test.tsx` – run red prior to code and green with no TypeScript errors afterward.
   - **Test-first Requirement:** Execute the above command (or per-file) to capture the failing assertions/type errors beforehand.
   - **Files Expected:** `frontend/src/components/Projects/AddWBE.tsx`, `AddProject.tsx`, `AddCostElement.tsx`, `AddChangeOrder.tsx` plus associated tests.
   - **Dependencies:** Step 1 (tests) and Step 2 (shared dialog props).

4. **Realign “Edit” forms with API contracts**
   - **Description:** Mirror Step 3 adjustments for `EditWBE`, `EditProject`, `EditCostElement`, `EditChangeOrder`, ensuring default values and validation errors only reference valid properties and RHF generics match the DTOs.
   - **Acceptance Criteria:** `pnpm test src/components/Projects/EditWBE.tsx src/components/Projects/EditProject.tsx src/components/Projects/EditCostElement.tsx src/components/Projects/EditChangeOrder.test.tsx` red first, then green with successful type check after edits.
   - **Test-first Requirement:** Run the above suites to confirm the current failures before modifying code.
   - **Files Expected:** `frontend/src/components/Projects/EditWBE.tsx`, `EditProject.tsx`, `EditCostElement.tsx`, `EditChangeOrder.tsx` (+ tests).
   - **Dependencies:** Steps 1–3.

5. **Type query-driven branch/version components**
   - **Description:** Introduce proper typings (interfaces or generated API types) for `BranchComparisonView.tsx`, `BranchMergePreview.tsx`, `VersionComparison.tsx`, `VersionHistoryViewer.tsx`, `RollbackVersion.tsx`, `RestoreEntity.tsx`, and `ViewBaseline` mocks. Ensure we narrow `useQuery` responses before property access and adjust mutations to concrete entity-specific functions.
   - **Acceptance Criteria:** Targeted tests (`pnpm test src/components/Projects/BranchComparisonView.test.tsx src/components/Projects/BranchMergePreview.test.tsx src/components/Projects/VersionComparison.test.tsx src/components/Projects/VersionHistoryViewer.test.tsx src/components/Projects/RollbackVersion.test.tsx src/components/Projects/RestoreEntity.test.tsx src/components/Projects/__tests__/ViewBaseline.test.tsx`) fail first and pass after updates; TypeScript no longer flags unknown types in these files.
   - **Test-first Requirement:** Run the combined command above (or per file) to confirm pre-change failures.
   - **Files Expected:** Listed components/tests.
   - **Dependencies:** Steps 1–4 (shared helpers/mocks).

6. **Validate end-to-end build**
   - **Description:** Execute `pnpm test` (full suite) followed by `pnpm build`. Address any remaining warnings/errors discovered at this stage.
   - **Acceptance Criteria:** Both commands succeed without TypeScript errors. Document any remaining flaky warnings (e.g., jsdom CSS parsing) for follow-up.
   - **Test-first Requirement:** `pnpm build` is currently red—re-run before any final tweaks to confirm baseline.
   - **Files Expected:** Any residual files uncovered by the final run.
   - **Dependencies:** Steps 1–5.

## TDD DISCIPLINE RULES

- Every step starts with a failing, targeted test (or the global build) before touching production code.
- Follow strict red → green → refactor cycles; do not batch unrelated fixes.
- Maximum of three attempts per step. If a step still fails after three red/green cycles, pause and request guidance.
- Tests must verify runtime behavior or type expectations—no changes solely to satisfy lint/TS without coverage.

## PROCESS CHECKPOINTS

- **After Step 2:** Pause and ask:
  1. Should we continue with the plan as-is?
  2. Have any assumptions been invalidated?
  3. Does the current state match our expectations?

- **After Step 5:** Repeat the same checkpoint questions before moving to the final validation.

## SCOPE BOUNDARIES

- Limit work to resolving the TypeScript/test failures enumerated above. Do not refactor unrelated components or introduce new features without explicit approval.
- If additional issues emerge outside this list, surface them and request confirmation before expanding scope.

## ROLLBACK STRATEGY

- **Safe rollback point:** Current `do/e5-003` branch before Step 1 changes (all edits tracked via git). Commit after each successful step to create intermediate rollback anchors.
- **If approach fails:** Revert to the latest stable commit and attempt a narrower strategy (e.g., fix tests/mocks first, then rebuild forms in smaller chunks), or consider splitting form rewrites into separate feature branches for focused review.
