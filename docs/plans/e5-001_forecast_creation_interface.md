# E5-001 Forecast Creation Interface Detailed Plan

---
## 1. Comprehensive User Stories

### As a Project Manager (PM)
- **Story:** I want to create and submit a new Estimate at Completion (EAC) forecast for my project so that I can formally communicate an updated projection of the total project cost based on the latest performance data and events.
- **Story:** I want to provide a detailed rationale and list of assumptions for each forecast to ensure that stakeholders who review it have the full context and understand the justification behind my EAC calculation.
- **Story:** I want to be able to edit a forecast I've created to correct any errors or update the rationale before it is formally reviewed.
- **Story:** I want to see a clear, chronological history of all forecasts submitted for my project, so I can track the evolution of the EAC and prepare for performance reviews.

### As a Program Director or Stakeholder
- **Story:** I want to review the complete forecast history for a project to understand its financial trajectory and the stability of its cost projections over time.
- **Story:** I want to be able to read the full rationale and assumptions for each forecast to properly evaluate the project's health and the credibility of the Project Manager's projections.

### As a System Administrator
- **Story:** I want all forecast data to be securely stored and linked to the correct project and author, ensuring a clear and auditable record of all financial projections.

---

## 2. Detailed UI/UX Design Description

### 2.1 Navigation and Access
- A new **"Forecasts" tab** will be added to the project detail page's main navigation, placed immediately after the "EVM" tab.
- Clicking this tab will display the `Forecasts History View`.

### 2.2 Forecasts History View (`ForecastsTable.tsx`)
- **Empty State:** When no forecasts exist for a project, the view will display a clear message (e.g., "No forecasts have been created for this project yet.") and a prominent "Create First Forecast" button.
- **Table View:**
    - The main feature of this view is a data table that lists all forecasts chronologically (newest first).
    - **Columns:**
        1.  `Creation Date`: The timestamp when the forecast was created.
        2.  `EAC (Estimate at Completion)`: The projected total cost, formatted as currency (e.g., $1,500,000.00).
        3.  `Rationale`: A truncated preview of the rationale text. The full text will be available via a tooltip or a popover on hover/click.
        4.  `Author`: The name of the user who created the forecast.
        5.  `Actions`: A dropdown menu for each row containing "Edit" and "Delete" options.
    - **Header:** The table header will contain a "Create New Forecast" button to launch the creation modal.

### 2.3 Create/Edit Forecast Modal (`AddForecast.tsx` / `EditForecast.tsx`)
- This modal will serve for both creating and editing a forecast, with the title changing accordingly ("Create New Forecast" or "Edit Forecast").
- **Form Fields:**
    1.  **Estimate at Completion (EAC):**
        -   **Type:** A required numeric input field.
        -   **Validation:** Must be a positive number. Real-time validation will show an error if non-numeric characters are entered or if the value is ≤ 0.
        -   **Label:** "Estimate at Completion (EAC)"
        -   **Help Text:** "Enter the new total estimated cost for the entire project upon completion."
    2.  **Rationale:**
        -   **Type:** A required, multi-line textarea that supports markdown for basic formatting.
        -   **Label:** "Rationale"
        -   **Help Text:** "Explain the justification for this new EAC. Reference specific performance trends (e.g., CPI/SPI), risks, change orders, or other events."
    3.  **Assumptions:**
        -   **Type:** An optional, multi-line textarea that also supports markdown.
        -   **Label:** "Assumptions"
        -   **Help Text:** "List any key assumptions made when determining this forecast (e.g., stable material costs, no further scope changes)."
- **Modal Actions:**
    - **"Save Forecast" button:** This is the primary action. It will be disabled until all required fields are valid.
    - **"Cancel" button:** Closes the modal without saving any changes.

### 2.4 User Workflow & Feedback
1.  The user navigates to the project detail page and clicks the "Forecasts" tab.
2.  The user clicks the "Create New Forecast" button.
3.  The `AddForecast` modal appears. The user fills out the form. The "Save" button becomes enabled once the EAC and Rationale are valid.
4.  The user clicks "Save Forecast." A loading indicator is shown.
5.  On success:
    - The modal closes.
    - A success toast notification appears (e.g., "Forecast created successfully.").
    - The `ForecastsTable` automatically refreshes to show the new entry at the top.
6.  On error:
    - The modal remains open.
    - An error toast notification appears with a descriptive message (e.g., "Error: Could not save forecast.").
7.  **Deleting a Forecast:**
    - The user clicks the "Delete" action from a row's menu.
    - A confirmation dialog appears: "Are you sure you want to delete this forecast? This action cannot be undone."
    - On confirmation, the forecast is deleted, and the table refreshes.

---

## 3. Implementation Checklist

A numbered checklist for implementing the full-stack Forecast Creation and Management feature, following Test-Driven Development (TDD) principles and process checkpoints.

### 3.1. Update Strategic Documents
- **Description:** Amend `docs/prd.md`, `docs/plan.md`, and `docs/project_status.md` to formally include the Forecast Management feature (E5-001).
- **Acceptance Criteria:**
    - PRD is updated to describe the user stories and functional requirements for creating, viewing, updating, and deleting forecasts (EAC, rationale, assumptions).
    - `project_status.md` shows E5-001 as "In Progress" under Sprint 6.
- **Test-First Requirement:** Not applicable (documentation-only change).
- **Expected Files:** `docs/prd.md`, `docs/project_status.md`.
- **Dependencies:** None.

### 3.2. Backend: Forecast Model and Schemas
- **Description:** Create the `Forecast` SQLModel, its associated Pydantic schemas (`Base`, `Create`, `Update`, `Public`), and define its relationship to the `Project` and `User` models.
- **Acceptance Criteria:**
    - The `Forecast` model includes fields for `id`, `eac`, `rationale`, `assumptions`, `project_id`, and `created_by_id`.
    - Pydantic schemas correctly represent the different data shapes for creation, updates, and public viewing.
    - The model passes all unit tests for creation, validation, and relationships.
- **Test-First Requirement:** Create a new test file `backend/tests/models/test_forecast.py` with a failing test that attempts to create and validate a `Forecast` instance before the model is implemented → **RED**.
- **Expected Files:** `backend/app/models/forecast.py` (new), `backend/tests/models/test_forecast.py` (new).
- **Dependencies:** Step 1 complete.

### 3.3. Backend: Database Migration
- **Description:** Generate and verify an Alembic migration script to create the `forecast` table in the database.
- **Acceptance Criteria:**
    - Running `alembic revision --autogenerate` successfully creates a new migration script.
    - The script accurately reflects the `Forecast` model schema, including columns, data types, foreign keys, and constraints.
    - The migration can be successfully applied (`upgrade`) and rolled back (`downgrade`).
- **Test-First Requirement:** Not applicable (build tool execution).
- **Expected Files:** New file in `backend/alembic/versions/`.
- **Dependencies:** Step 2.

### 3.4. Backend: CRUD API Router
- **Description:** Implement a new FastAPI router at `/api/v1/projects/{project_id}/forecasts` providing full CRUD functionality for `Forecast` entities, scoped to a specific project.
- **Acceptance Criteria:**
    - API endpoints for `Create`, `List`, `Update`, and `Delete` are implemented and functional.
    - All endpoints correctly authorize the user and ensure they have access to the specified project.
    - The API returns correct HTTP status codes and error responses for invalid requests.
- **Test-First Requirement:** Create `backend/tests/api/routes/test_forecasts.py` with failing integration tests for each CRUD endpoint (e.g., a `POST` request to the create endpoint fails with a 404) before the router is implemented → **RED**.
- **Expected Files:** `backend/app/api/routes/forecasts.py` (new), `backend/tests/api/routes/test_forecasts.py` (new), `backend/app/api/main.py` (updated to include router).
- **Dependencies:** Step 3.

> ### Process Checkpoint #1 (after Step 4)
> - **Continue as planned?** Yes.
> - **Have any assumptions been invalidated?** No, the standard CRUD pattern is applicable here.
> - **Does the current state match expectations?** The backend should now have a fully functional and tested API for managing forecasts, with supporting documentation updated.

### 3.5. Frontend: API Client Regeneration
- **Description:** Regenerate the frontend's OpenAPI client to include the new `ForecastsService` and its associated types.
- **Acceptance Criteria:**
    - The `frontend/src/client` directory is updated with new service methods and TypeScript types for `Forecast`.
    - The project's TypeScript compilation passes without errors after regeneration.
- **Test-First Requirement:** Not applicable (build tool execution).
- **Expected Files:** `frontend/src/client/**`.
- **Dependencies:** Step 4.

### 3.6. Frontend: Tab, Table, and Data Fetching
- **Description:** Create a new "Forecasts" tab on the project detail page, containing a `ForecastsTable` component that lists all forecasts for that project.
- **Acceptance Criteria:**
    - A "Forecasts" tab appears in the project view.
    - The `ForecastsTable` component correctly fetches and displays a list of forecasts using the generated `ForecastsService`.
    - The table displays columns for EAC, Rationale, and includes an actions menu (for Edit/Delete).
    - A "Create Forecast" button is present in the table's header area.
- **Test-First Requirement:** Create `frontend/src/components/Projects/ForecastsTable.test.tsx` with a failing test that attempts to render the component and expects a table structure → **RED**.
- **Expected Files:** `frontend/src/routes/projects_.$projectId.tsx` (updated), `frontend/src/components/Projects/ForecastsTable.tsx` (new), `frontend/src/components/Projects/ForecastsTable.test.tsx` (new).
- **Dependencies:** Step 5.

### 3.7. Frontend: Add/Edit Modal Components
- **Description:** Build the `AddForecast` and `EditForecast` modal forms using Chakra UI and React Hook Form, following the existing pattern of `AddCostRegistration`.
- **Acceptance Criteria:**
    - The modals contain validated input fields for EAC, Rationale, and Assumptions.
    - Form submission is handled by a TanStack Query mutation that calls the appropriate `ForecastsService` method.
    - On successful submission, the forecasts query is invalidated to refresh the `ForecastsTable`.
- **Test-First Requirement:** Create `frontend/src/components/Projects/AddForecast.test.tsx` with a failing test that renders the form and checks for input fields and a submit button → **RED**.
- **Expected Files:** `frontend/src/components/Projects/AddForecast.tsx` (new), `frontend/src/components/Projects/EditForecast.tsx` (new), `frontend/src/components/Projects/AddForecast.test.tsx` (new).
- **Dependencies:** Step 6.

> ### Process Checkpoint #2 (after Step 7)
> - **Continue as planned?** Yes.
> - **Are backend/UX integrations functioning together?** The API should be successfully serving data to the new frontend components.
> - **Any unexpected regressions or scope issues?** No, the feature is self-contained.

### 3.8. Comprehensive E2E Testing
- **Description:** Write a Playwright end-to-end test to simulate the complete user workflow for managing forecasts.
- **Acceptance Criteria:**
    - The test successfully navigates to the forecasts tab.
    - It creates a new forecast and verifies its appearance in the table.
    - It edits the forecast and verifies the update.
    - It deletes the forecast and verifies its removal.
    - The entire backend and frontend test suites pass without any new failures.
- **Test-First Requirement:** Create a failing Playwright test in `frontend/tests/forecasts.spec.ts` that fails to find the "Forecasts" tab or the "Create Forecast" button → **RED**.
- **Expected Files:** `frontend/tests/forecasts.spec.ts` (new).
- **Dependencies:** Steps 1-7.

---

## TDD Discipline Rules
1.  Every code step must begin with a failing automated test that covers the intended behavior.
2.  Strictly follow **Red → Green → Refactor** cycles.
3.  If a step fails more than three times, halt and re-evaluate the approach.
4.  Tests must assert specific behaviors and outputs.

## Rollback Strategy
- **Safe Rollback Point:** The feature is additive. It can be safely rolled back at any point before the final merge by reverting the corresponding commits for each step.
- **DB Rollback:** The database change can be reverted by running the `downgrade` version of the Alembic migration script created in Step 3.
