# High-Level Analysis: E5-003 Change Order Entry Interface

**Task:** E5-003 (Change Order Entry Interface)
**Status:** Analysis Phase - User Stories and UI/UX Definition
**Date:** 2025-11-23T15:18:15+01:00
**Analysis Code:** E50003

---

## Objective

Define detailed user stories and user interface experience for E5-003 (Change Order Entry Interface), enabling project managers to document scope changes, contract modifications, and customer-requested additions with comprehensive financial impact tracking, supporting complete change order lifecycle management from draft through implementation.

---

## User Story

### Primary User Story

**As a** project manager
**I want to** create and manage change orders documenting scope changes with financial impacts and workflow status tracking
**So that** I can maintain proper change control, track budget and revenue adjustments, preserve baseline integrity for variance analysis, and ensure all scope modifications are properly documented and approved before implementation.

### Secondary User Stories

**As a** project controller
**I want to** view all change orders for a project with their current status and financial impacts
**So that** I can track change order trends, assess cumulative impact on project budgets, and prepare change order reports for stakeholders.

**As a** department manager
**I want to** create change orders with detailed justification and impact analysis
**So that** I can document scope changes affecting my department's work and provide transparent rationale for budget adjustments.

**As an** executive
**I want to** see approved and implemented change orders with their financial impacts aggregated at project level
**So that** I can assess overall project scope changes and their effect on project profitability.

**As a** customer representative
**I want to** see change orders requested by my organization with their approval status
**So that** I can track the status of requested changes and understand their financial implications.

**As a** finance manager
**I want to** review change orders before implementation to validate budget and revenue adjustments
**So that** I can ensure financial integrity and proper accounting treatment of scope changes.

### Change Order Project Element Modification User Stories

**As a** project manager
**I want to** create change orders that add new WBEs or cost elements to a project
**So that** I can document scope expansions when customers request additional machines or work packages, and track the financial impact of these additions.

**As a** project manager
**I want to** create change orders that modify existing WBEs or cost elements (budgets, revenues, schedules)
**So that** I can document scope adjustments, budget revisions, and revenue reallocations while maintaining a clear audit trail of what changed and why.

**As a** project manager
**I want to** create change orders that remove WBEs or cost elements from a project
**So that** I can document scope reductions when work is cancelled or deferred, and track the financial impact of these removals.

**As a** project controller
**I want to** see baseline snapshots showing the project structure before and after change order execution
**So that** I can compare how WBEs and cost elements changed, analyze the impact on project structure, and generate variance reports showing structural changes over time.

**As a** project manager
**I want to** see a visual comparison of project structure before and after change order approval
**So that** I can verify that all intended changes are correctly captured and understand the full scope of modifications before execution.

**As a** finance manager
**I want to** review change orders that modify project elements with detailed before/after financial comparisons
**So that** I can validate that budget and revenue adjustments are accurate and properly documented before approval.

---

## Change Order Project Element Modification - Detailed Description

### Overview

Change orders can modify the project structure by creating, updating, or deleting WBEs and cost elements. The system tracks these structural changes through a baselining mechanism that captures the "before" and "after" state, enabling historical comparison and variance analysis.

### Modification Operations

**1. Create New Project Elements**
- **WBE Creation:** Add new machines or deliverables to the project
  - Example: Customer requests additional machine type "Assembly Station B"
  - Line item specifies: `operation_type: "create"`, `target_type: "wbe"`, with new WBE attributes (machine_type, revenue_allocation, etc.)

- **Cost Element Creation:** Add new cost elements to existing or new WBEs
  - Example: Add "Software Development" cost element to existing WBE
  - Line item specifies: `operation_type: "create"`, `target_type: "cost_element"`, with new cost element attributes (department, budget_bac, revenue_plan, etc.)

**2. Update Existing Project Elements**
- **WBE Updates:** Modify WBE attributes (revenue_allocation, status, delivery_date, etc.)
  - Example: Increase revenue allocation for existing WBE due to scope expansion
  - Line item specifies: `operation_type: "update"`, `target_type: "wbe"`, `target_id: <wbe_id>`, with updated attributes

- **Cost Element Updates:** Modify cost element attributes (budget_bac, revenue_plan, schedule, etc.)
  - Example: Increase budget for "Mechanical Engineering" cost element
  - Line item specifies: `operation_type: "update"`, `target_type: "cost_element"`, `target_id: <cost_element_id>`, with budget_change and revenue_change values

**3. Delete Project Elements**
- **WBE Deletion:** Remove machines or deliverables from project
  - Example: Customer cancels one machine from the order
  - Line item specifies: `operation_type: "delete"`, `target_type: "wbe"`, `target_id: <wbe_id>`

- **Cost Element Deletion:** Remove cost elements from WBEs
  - Example: Remove "Procurement" cost element that is no longer needed
  - Line item specifies: `operation_type: "delete"`, `target_type: "cost_element"`, `target_id: <cost_element_id>`

### Design Phase - Staged Changes via Temporary Staging Project

**Critical Requirement:** During the "design" phase, all changes to WBEs and cost elements are staged in a **temporary staging project** that mirrors the actual project structure. Changes do NOT affect the actual project data until approval and execution.

**Implementation Approach:**
- **Staging Project Creation:** When a change order is created, system automatically creates a temporary staging project
  - Staging project is a copy/snapshot of the actual project structure
  - All WBEs and cost elements from the actual project are copied to the staging project
  - Staging project is marked with `is_staging=True` flag and linked to change order
  - Staging project has its own project_id but is not visible in normal project lists

- **Staged Modifications:** Users modify WBEs and cost elements directly in the staging project
  - CREATE: Add new WBEs/cost elements to staging project
  - UPDATE: Modify existing WBEs/cost elements in staging project
  - DELETE: Remove WBEs/cost elements from staging project
  - All modifications happen in the staging project, not the actual project

- **Change Order Line Items:** Line items reference elements in the staging project
  - Line items track which elements were created/modified/deleted
  - Line items point to staging project elements via foreign keys
  - Line items can reference both actual project elements (for updates) and staging elements (for creates)

- **Preview and Comparison:** Users can compare staging project vs actual project
  - Side-by-side comparison shows differences
  - Visual diff highlights changes
  - Financial impact calculated from staging project state

- **No Impact on Actual Project:** Actual project remains unchanged during design phase
  - EVM calculations use actual project data
  - Reports show actual project state
  - Staging project is isolated and invisible to normal operations

**User Experience:**
- Users work directly with staging project structure (feels like working with real project)
- Changes are immediately visible in staging project
- Preview shows comparison between staging and actual project
- Users can iterate on changes without affecting live project
- Staging project can be discarded if change order is cancelled

### Staging Project Architecture

**Purpose:** Provide a temporary project structure where all change order modifications are staged before being applied to the actual project.

**Staging Project Model:**
```python
class Project:
    project_id: UUID (PK)
    project_name: str
    # ... all standard project fields ...
    is_staging: bool = False  # New field: True for staging projects
    staging_for_change_order_id: UUID | None (FK → ChangeOrder, NULL for normal projects)
    staging_for_project_id: UUID | None (FK → Project, NULL for normal projects)
    # Links staging project to change order and original project
```

**Staging Project Lifecycle:**

1. **Creation (Change Order Created - "design" status):**
   - System creates staging project with `is_staging=True`
   - Copies all WBEs from actual project to staging project
   - Copies all cost elements from actual project to staging project
   - Links staging project to change order via `staging_for_change_order_id`
   - Links staging project to original project via `staging_for_project_id`
   - Staging project is hidden from normal project lists (filtered by `is_staging=False`)

2. **Modification (Design Phase):**
   - Users modify staging project structure directly
   - CREATE: Add new WBEs/cost elements to staging project
   - UPDATE: Modify WBEs/cost elements in staging project
   - DELETE: Remove WBEs/cost elements from staging project
   - Line items track which operations were performed
   - Actual project remains unchanged

3. **Approval Request (design → approve):**
   - System creates "before" baseline snapshot of actual project
   - Staging project is locked (read-only)
   - Changes cannot be modified further
   - Comparison between staging and actual project is finalized

4. **Approval Completion (approve → execute):**
   - System applies staging project changes to actual project:
     - CREATE: Copy new elements from staging to actual project
     - UPDATE: Apply modifications from staging to actual project
     - DELETE: Remove elements from actual project (if they exist in actual but not in staging)
   - System creates "after" baseline snapshot of actual project
   - Staging project can be archived or deleted (optional)

5. **Cancellation (if change order is cancelled):**
   - Staging project can be deleted
   - No impact on actual project

### Baselining Mechanism for Change Tracking

**Purpose:** Capture project structure state before and after change order approval to enable historical comparison and variance analysis.

**Baseline Creation Triggers:**
1. **On Approval Request:** When change order status transitions from "design" to "approve"
   - System creates "before" baseline snapshot
   - Captures current state of all WBEs and cost elements in the **actual project**
   - Baseline type: "change_order_before"
   - Links to change order via `change_order_id` reference
   - **Note:** Staging project is locked, but changes still NOT applied to actual project

2. **On Approval Completion:** When change order status transitions from "approve" to "execute"
   - System applies all modifications from staging project to actual project
   - System creates "after" baseline snapshot
   - Captures new state of actual project after all modifications are applied
   - Baseline type: "change_order_after"
   - Links to change order via `change_order_id` reference
   - **Note:** This is when changes actually affect actual project data

**Baseline Snapshot Content:**
- **Project Structure:** Complete list of WBEs and cost elements
- **Financial State:** Budget allocations, revenue allocations for each element
- **Schedule State:** Cost element schedules (start_date, end_date, progression_type)
- **EVM State:** Current earned value, percent complete for each cost element
- **Metadata:** Timestamp, user who triggered the change, change order reference

**Comparison Capabilities:**
- Compare "before" baseline vs "after" baseline to see:
  - Which WBEs/cost elements were added, modified, or removed
  - Financial impact (budget changes, revenue changes)
  - Structural changes (new hierarchy, removed elements)
  - Schedule impact (modified timelines)
- Compare any baseline vs current state to see:
  - How project has evolved since change order execution
  - Cumulative impact of multiple change orders
  - Variance from original baseline

**Implementation Approach:**
- Reuse existing Baseline Log and Baseline Cost Element infrastructure
- Create baseline snapshots automatically on status transitions
- Store change order reference in baseline metadata
- Enable baseline comparison UI to show change order context
- Link baseline comparisons to change order detail views

### Change Order Line Item Model Design (Revised for Staging Project)

**Simplified Line Item Schema:**
```python
class ChangeOrderLineItemBase:
    change_order_id: UUID (FK → ChangeOrder)
    operation_type: str (ENUM: "create", "update", "delete", "financial_adjustment")
    target_type: str (ENUM: "wbe", "cost_element")

    # Reference to element in STAGING project
    staging_target_id: UUID | None (FK → WBE or CostElement in staging project)

    # Reference to original element in ACTUAL project (for update/delete operations)
    actual_target_id: UUID | None (FK → WBE or CostElement in actual project, NULL if create)

    # Financial changes (calculated from staging vs actual)
    budget_change: Decimal | None (change to budget, can be negative)
    revenue_change: Decimal | None (change to revenue, can be negative)

    description: str | None
    sequence_number: int (order of operations within change order)
```

**Key Changes:**
- **No JSON storage:** Elements are stored directly in staging project using existing models
- **staging_target_id:** Points to WBE or cost element in staging project (always exists after creation)
- **actual_target_id:** Points to original element in actual project (NULL for create operations)
- **Simpler relationships:** All elements use standard foreign key relationships
- **Direct modification:** Users modify staging project elements directly, line items just track what changed

### Relationship Model: Change Order Line Items ↔ WBEs/Cost Elements (Staging Project Approach)

**Key Concept:** Change order line items reference elements in the **staging project**, which is a temporary copy of the actual project. All modifications happen in the staging project, and relationships are always direct foreign keys (no conditional relationships needed).

#### Relationship Types by Operation (Staging Project Approach)

**1. CREATE Operations**
- **Staging Relationship:** Foreign key to new element in staging project
- **staging_target_id:** `NOT NULL` (foreign key to WBE or CostElement in staging project)
- **actual_target_id:** `NULL` (element doesn't exist in actual project yet)
- **target_type:** Specifies what was created ("wbe" or "cost_element")
- **Data Storage:** Element stored directly in staging project using standard WBE/CostElement models
- **Execution:** When change order is executed, element is copied from staging project to actual project
- **After Execution:** New element created in actual project, line item preserves staging reference (historical)

**2. UPDATE Operations**
- **Staging Relationship:** Foreign key to modified element in staging project
- **actual_target_id:** `NOT NULL` (foreign key to original element in actual project)
- **staging_target_id:** `NOT NULL` (foreign key to modified element in staging project)
- **target_type:** Specifies which table the foreign keys reference
- **Validation:** Both staging and actual elements must exist before change order can be approved
- **Execution:** When change order is executed, modifications from staging element are applied to actual element
- **Relationship:** Direct foreign key relationships to both staging and actual elements

**3. DELETE Operations**
- **Staging Relationship:** Element removed from staging project (no staging_target_id)
- **actual_target_id:** `NOT NULL` (foreign key to element in actual project that will be deleted)
- **staging_target_id:** `NULL` (element doesn't exist in staging project)
- **target_type:** Specifies which table the foreign key references
- **Validation:** Actual element must exist before change order can be approved
- **Execution:** When change order is executed, element is deleted from actual project
- **Relationship:** Direct foreign key relationship to actual element (preserved for historical record)

**4. FINANCIAL_ADJUSTMENT Operations**
- **Staging Relationship:** Foreign key to modified cost element in staging project
- **actual_target_id:** `NOT NULL` (foreign key to original cost element in actual project)
- **staging_target_id:** `NOT NULL` (foreign key to modified cost element in staging project)
- **target_type:** Must be "cost_element"
- **Validation:** Both staging and actual cost elements must exist
- **Execution:** When change order is executed, only financial attributes from staging are applied to actual
- **Relationship:** Direct foreign key relationships to both staging and actual cost elements

#### Database Schema Design

```python
class ChangeOrderLineItem(ChangeOrderLineItemBase, table=True):
    """Change Order Line Item database model."""

    change_order_line_id: UUID (PK)
    change_order_id: UUID (FK → ChangeOrder, NOT NULL)

    # Conditional foreign keys based on operation_type
    target_wbe_id: UUID | None (FK → WBE, NULL if target_type != "wbe" OR operation_type == "create")
    target_cost_element_id: UUID | None (FK → CostElement, NULL if target_type != "cost_element" OR operation_type == "create")

    # For financial_adjustment operations
    cost_element_id: UUID | None (FK → CostElement, NULL if operation_type != "financial_adjustment")

    # Relationships (conditional loading)
    change_order: ChangeOrder | None = Relationship()
    target_wbe: WBE | None = Relationship(foreign_keys="[ChangeOrderLineItem.target_wbe_id]")
    target_cost_element: CostElement | None = Relationship(foreign_keys="[ChangeOrderLineItem.target_cost_element_id]")
    financial_adjustment_cost_element: CostElement | None = Relationship(foreign_keys="[ChangeOrderLineItem.cost_element_id]")
```

**Recommended Schema (Staging Project Approach):**
```python
class ChangeOrderLineItem(ChangeOrderLineItemBase, table=True):
    """Change Order Line Item database model."""

    change_order_line_id: UUID (PK)
    change_order_id: UUID (FK → ChangeOrder, NOT NULL)

    # Reference to element in staging project (always exists after creation)
    staging_target_wbe_id: UUID | None (FK → WBE in staging project)
    staging_target_cost_element_id: UUID | None (FK → CostElement in staging project)

    # Reference to original element in actual project (NULL for create operations)
    actual_target_wbe_id: UUID | None (FK → WBE in actual project)
    actual_target_cost_element_id: UUID | None (FK → CostElement in actual project)

    # Relationships
    change_order: ChangeOrder | None = Relationship()
    staging_target_wbe: WBE | None = Relationship(foreign_keys="[ChangeOrderLineItem.staging_target_wbe_id]")
    staging_target_cost_element: CostElement | None = Relationship(foreign_keys="[ChangeOrderLineItem.staging_target_cost_element_id]")
    actual_target_wbe: WBE | None = Relationship(foreign_keys="[ChangeOrderLineItem.actual_target_wbe_id]")
    actual_target_cost_element: CostElement | None = Relationship(foreign_keys="[ChangeOrderLineItem.actual_target_cost_element_id]")
```

**Benefits of Staging Project Approach:**
- **Simpler relationships:** All elements use standard foreign keys (no conditional logic)
- **No JSON storage:** Elements stored in database using existing models
- **Direct modification:** Users work with real project structure (staging project)
- **Better validation:** Can validate staging project structure using existing validation rules
- **Easier comparison:** Compare staging project vs actual project directly
- **Cleaner execution:** Copy elements from staging to actual (simpler than parsing JSON)

#### Relationship Validation Rules

1. **CREATE Operations:**
   - `target_id` MUST be `NULL`
   - `target_type` MUST be specified ("wbe" or "cost_element")
   - `new_wbe_data` or `new_cost_element_data` MUST be provided
   - No foreign key relationship exists (element doesn't exist yet)

2. **UPDATE Operations:**
   - `target_id` MUST NOT be `NULL`
   - `target_type` MUST be specified ("wbe" or "cost_element")
   - Target element MUST exist in database
   - Foreign key relationship exists to existing element

3. **DELETE Operations:**
   - `target_id` MUST NOT be `NULL`
   - `target_type` MUST be specified ("wbe" or "cost_element")
   - Target element MUST exist in database
   - Foreign key relationship exists to existing element
   - After execution, element is deleted but line item preserves reference

4. **FINANCIAL_ADJUSTMENT Operations:**
   - `target_id` MUST be `NULL` (not used)
   - `target_type` MUST be "cost_element"
   - `cost_element_id` MUST NOT be `NULL`
   - Cost element MUST exist in database
   - Foreign key relationship exists via `cost_element_id`

#### Relationship Summary Table

| Operation Type | target_id | target_type | cost_element_id | Relationship Type | Notes |
|---------------|-----------|-------------|-----------------|-------------------|-------|
| create (WBE) | NULL | "wbe" | NULL | None | Element created on execution |
| create (Cost Element) | NULL | "cost_element" | NULL | None | Element created on execution |
| update (WBE) | NOT NULL | "wbe" | NULL | FK → WBE | Direct relationship |
| update (Cost Element) | NOT NULL | "cost_element" | NULL | FK → CostElement | Direct relationship |
| delete (WBE) | NOT NULL | "wbe" | NULL | FK → WBE | Direct relationship (historical after deletion) |
| delete (Cost Element) | NOT NULL | "cost_element" | NULL | FK → CostElement | Direct relationship (historical after deletion) |
| financial_adjustment | NULL | "cost_element" | NOT NULL | FK → CostElement (via cost_element_id) | Direct relationship |

---

## Relationship Examples by Operation Type

### Example 1: CREATE WBE Operation (Staging Project Approach)

**Scenario:** Customer requests an additional "Assembly Station B" machine for the project.

**Staging Project Setup:**
- Staging project created with copy of all actual project WBEs and cost elements
- Staging project ID: "770e8400-e29b-41d4-a716-446655440000"
- Actual project ID: "440e8400-e29b-41d4-a716-446655440000"

**Design Phase:**
- User adds new WBE to staging project using standard WBE creation form:
  ```python
  WBE(
      wbe_id: "880e8400-e29b-41d4-a716-446655440001",  # New UUID in staging project
      project_id: "770e8400-e29b-41d4-a716-446655440000",  # Staging project
      machine_type: "Assembly Station B",
      revenue_allocation: 150000.00,
      delivery_date: "2025-06-30",
      status: "designing"
  )
  ```
- System automatically creates line item:
  ```python
  ChangeOrderLineItem(
      change_order_line_id: "550e8400-e29b-41d4-a716-446655440001",
      change_order_id: "550e8400-e29b-41d4-a716-446655440000",
      operation_type: "create",
      target_type: "wbe",
      staging_target_wbe_id: "880e8400-e29b-41d4-a716-446655440001",  # FK to staging WBE
      actual_target_wbe_id: NULL,  # Doesn't exist in actual project yet
      budget_change: NULL,
      revenue_change: 150000.00,  # Calculated from staging WBE
      description: "Add new Assembly Station B as requested by customer",
      sequence_number: 1
  )
  ```
- **Foreign key relationship exists:** `staging_target_wbe_id` → WBE in staging project
- Preview shows: "Will create new WBE: Assembly Station B (revenue: €150,000.00)"
- **No actual project impact:** Actual project unchanged, WBE only exists in staging

**Execution Phase (approve → execute):**
- System compares staging project vs actual project
- Detects new WBE in staging (doesn't exist in actual)
- Copies WBE from staging to actual project:
  ```python
  WBE(
      wbe_id: "990e8400-e29b-41d4-a716-446655440001",  # New UUID in actual project
      project_id: "440e8400-e29b-41d4-a716-446655440000",  # Actual project
      machine_type: "Assembly Station B",
      revenue_allocation: 150000.00,
      delivery_date: "2025-06-30",
      status: "designing"
  )
  ```
- Line item preserves staging reference: `staging_target_wbe_id` still points to staging WBE
- **No backward relationship:** New actual WBE has no reference to line item (by design)
- **Project impact:** New WBE now exists in actual project

---

### Example 2: CREATE Cost Element Operation (Staging Project Approach)

**Scenario:** Add "Software Development" cost element to existing WBE.

**Staging Project Setup:**
- Staging project created with copy of all actual project WBEs and cost elements
- Staging WBE ID: "aa0e8400-e29b-41d4-a716-446655440000" (copy of actual WBE)

**Design Phase:**
- User adds new cost element to staging project using standard cost element creation form:
  ```python
  CostElement(
      cost_element_id: "dd0e8400-e29b-41d4-a716-446655440001",  # New UUID in staging project
      wbe_id: "aa0e8400-e29b-41d4-a716-446655440000",  # Staging WBE
      project_id: "770e8400-e29b-41d4-a716-446655440000",  # Staging project
      department_code: "SW",
      department_name: "Software Development",
      cost_element_type_id: "220e8400-e29b-41d4-a716-446655440000",
      budget_bac: 50000.00,
      revenue_plan: 60000.00
  )
  ```
- System automatically creates line item:
  ```python
  ChangeOrderLineItem(
      change_order_line_id: "550e8400-e29b-41d4-a716-446655440002",
      change_order_id: "550e8400-e29b-41d4-a716-446655440000",
      operation_type: "create",
      target_type: "cost_element",
      staging_target_cost_element_id: "dd0e8400-e29b-41d4-a716-446655440001",  # FK to staging
      actual_target_cost_element_id: NULL,  # Doesn't exist in actual project yet
      budget_change: 50000.00,  # Calculated from staging cost element
      revenue_change: 60000.00,  # Calculated from staging cost element
      description: "Add Software Development department to WBE",
      sequence_number: 2
  )
  ```
- **Foreign key relationship exists:** `staging_target_cost_element_id` → CostElement in staging project
- Preview shows: "Will create new Cost Element: Software Development in WBE [WBE-001] (budget: €50,000.00, revenue: €60,000.00)"
- **No actual project impact:** Actual project unchanged, cost element only exists in staging

**Execution Phase:**
- System compares staging project vs actual project
- Detects new cost element in staging (doesn't exist in actual)
- Copies cost element from staging to actual project:
  ```python
  CostElement(
      cost_element_id: "ee0e8400-e29b-41d4-a716-446655440001",  # New UUID in actual project
      wbe_id: "330e8400-e29b-41d4-a716-446655440000",  # Actual WBE
      project_id: "440e8400-e29b-41d4-a716-446655440000",  # Actual project
      department_code: "SW",
      department_name: "Software Development",
      budget_bac: 50000.00,
      revenue_plan: 60000.00
  )
  ```
- Line item preserves staging reference: `staging_target_cost_element_id` still points to staging cost element
- **No backward relationship:** New actual cost element has no reference to line item (by design)
- **Project impact:** New cost element now exists in actual project WBE

---

### Example 3: UPDATE WBE Operation

**Scenario:** Increase revenue allocation for existing WBE due to scope expansion.

**Line Item Data (Design Phase):**
```python
ChangeOrderLineItem(
    change_order_line_id: "550e8400-e29b-41d4-a716-446655440003",
    change_order_id: "550e8400-e29b-41d4-a716-446655440000",
    operation_type: "update",
    target_type: "wbe",
    target_id: "330e8400-e29b-41d4-a716-446655440000",  # Existing WBE UUID
    target_wbe_id: "330e8400-e29b-41d4-a716-446655440000",  # FK relationship
    target_cost_element_id: NULL,
    cost_element_id: NULL,
    new_wbe_data: NULL,  # Not applicable
    budget_change: NULL,  # Not applicable for WBE updates
    revenue_change: 25000.00,  # Increase revenue by €25,000
    description: "Increase revenue allocation due to additional features",
    sequence_number: 3
)
```

**Design Phase:**
- Line item stored with `target_id` pointing to existing WBE
- **Foreign key relationship exists:** `target_wbe_id` → WBE.wbe_id
- System can load existing WBE via relationship:
  ```python
  existing_wbe = line_item.target_wbe  # Loads WBE via FK
  # existing_wbe.revenue_allocation = 100000.00 (current value)
  ```
- Preview shows: "Will update WBE [WBE-001]: revenue_allocation 100000.00 → 125000.00"
- **No project impact:** WBE data unchanged

**Execution Phase:**
- System loads existing WBE via `target_id`:
  ```python
  wbe = session.get(WBE, line_item.target_id)
  # wbe.revenue_allocation = 100000.00 (before)
  ```
- Applies changes:
  ```python
  wbe.revenue_allocation += line_item.revenue_change
  # wbe.revenue_allocation = 125000.00 (after)
  ```
- Updates WBE in database
- **Foreign key relationship maintained:** `target_wbe_id` still points to same WBE
- **Project impact:** WBE revenue_allocation updated

---

### Example 4: UPDATE Cost Element Operation

**Scenario:** Increase budget for "Mechanical Engineering" cost element.

**Line Item Data (Design Phase):**
```python
ChangeOrderLineItem(
    change_order_line_id: "550e8400-e29b-41d4-a716-446655440004",
    change_order_id: "550e8400-e29b-41d4-a716-446655440000",
    operation_type: "update",
    target_type: "cost_element",
    target_id: "440e8400-e29b-41d4-a716-446655440000",  # Existing Cost Element UUID
    target_wbe_id: NULL,
    target_cost_element_id: "440e8400-e29b-41d4-a716-446655440000",  # FK relationship
    cost_element_id: NULL,
    new_cost_element_data: NULL,
    budget_change: 15000.00,  # Increase budget by €15,000
    revenue_change: 18000.00,  # Increase revenue by €18,000
    description: "Increase budget and revenue for Mechanical Engineering",
    sequence_number: 4
)
```

**Design Phase:**
- Line item stored with `target_id` pointing to existing cost element
- **Foreign key relationship exists:** `target_cost_element_id` → CostElement.cost_element_id
- System can load existing cost element:
  ```python
  existing_ce = line_item.target_cost_element
  # existing_ce.budget_bac = 80000.00 (current)
  # existing_ce.revenue_plan = 90000.00 (current)
  ```
- Preview shows: "Will update Cost Element [CE-001]: budget 80000.00 → 95000.00, revenue 90000.00 → 108000.00"
- **No project impact:** Cost element data unchanged

**Execution Phase:**
- System loads existing cost element:
  ```python
  cost_element = session.get(CostElement, line_item.target_id)
  # cost_element.budget_bac = 80000.00 (before)
  # cost_element.revenue_plan = 90000.00 (before)
  ```
- Applies changes:
  ```python
  cost_element.budget_bac += line_item.budget_change
  cost_element.revenue_plan += line_item.revenue_change
  # cost_element.budget_bac = 95000.00 (after)
  # cost_element.revenue_plan = 108000.00 (after)
  ```
- Updates cost element in database
- **Foreign key relationship maintained**
- **Project impact:** Cost element budget and revenue updated

---

### Example 5: DELETE WBE Operation (Staging Project Approach)

**Scenario:** Customer cancels one machine from the order.

**Staging Project Setup:**
- Staging project created with copy of actual project
- Actual WBE ID: "330e8400-e29b-41d4-a716-446655440001" (Assembly Station A, revenue: 50000.00)
- Staging WBE ID: "bb0e8400-e29b-41d4-a716-446655440001" (copy of actual)

**Design Phase:**
- User deletes WBE from staging project using standard delete operation:
  ```python
  # WBE removed from staging project
  staging_wbe = session.get(WBE, "bb0e8400-e29b-41d4-a716-446655440001")
  session.delete(staging_wbe)
  # WBE no longer exists in staging project
  ```
- System automatically creates/updates line item:
  ```python
  ChangeOrderLineItem(
      change_order_line_id: "550e8400-e29b-41d4-a716-446655440005",
      change_order_id: "550e8400-e29b-41d4-a716-446655440000",
      operation_type: "delete",
      target_type: "wbe",
      staging_target_wbe_id: NULL,  # WBE doesn't exist in staging (deleted)
      actual_target_wbe_id: "330e8400-e29b-41d4-a716-446655440001",  # FK to actual WBE
      budget_change: NULL,
      revenue_change: -50000.00,  # Negative impact (revenue removed)
      description: "Remove Assembly Station A as cancelled by customer",
      sequence_number: 5
  )
  ```
- **Foreign key relationship exists:** `actual_target_wbe_id` → WBE in actual project
- System validates WBE exists in actual project and can be safely deleted:
  ```python
  actual_wbe = line_item.actual_target_wbe
  # Check if WBE has cost elements, cost registrations, etc.
  ```
- Preview shows: "Will delete WBE [WBE-002]: Assembly Station A (revenue: -50000.00)"
- **No actual project impact:** Actual WBE still exists

**Execution Phase:**
- System compares staging project vs actual project
- Detects WBE exists in actual but not in staging (deleted from staging)
- Deletes WBE from actual project:
  ```python
  actual_wbe = session.get(WBE, line_item.actual_target_wbe_id)
  # actual_wbe.machine_type = "Assembly Station A"
  session.delete(actual_wbe)
  session.commit()
  ```
- **Foreign key relationship preserved:** Line item `actual_target_wbe_id` still contains WBE UUID (historical record)
- **Note:** After deletion, FK may become invalid, but line item preserves reference for audit trail
- **Project impact:** WBE and its cost elements deleted from actual project

---

### Example 6: DELETE Cost Element Operation (Staging Project Approach)

**Scenario:** Remove "Procurement" cost element that is no longer needed.

**Staging Project Setup:**
- Staging project created with copy of actual project
- Actual Cost Element ID: "440e8400-e29b-41d4-a716-446655440001" (Procurement, budget: 20000.00, revenue: 22000.00)
- Staging Cost Element ID: "cc0e8400-e29b-41d4-a716-446655440001" (copy of actual)

**Design Phase:**
- User deletes cost element from staging project using standard delete operation:
  ```python
  # Cost element removed from staging project
  staging_ce = session.get(CostElement, "cc0e8400-e29b-41d4-a716-446655440001")
  session.delete(staging_ce)
  # Cost element no longer exists in staging project
  ```
- System automatically creates/updates line item:
  ```python
  ChangeOrderLineItem(
      change_order_line_id: "550e8400-e29b-41d4-a716-446655440006",
      change_order_id: "550e8400-e29b-41d4-a716-446655440000",
      operation_type: "delete",
      target_type: "cost_element",
      staging_target_cost_element_id: NULL,  # Cost element doesn't exist in staging (deleted)
      actual_target_cost_element_id: "440e8400-e29b-41d4-a716-446655440001",  # FK to actual
      budget_change: -20000.00,  # Negative impact (budget removed)
      revenue_change: -22000.00,  # Negative impact (revenue removed)
      description: "Remove Procurement cost element - work outsourced",
      sequence_number: 6
  )
  ```
- **Foreign key relationship exists:** `actual_target_cost_element_id` → CostElement in actual project
- System validates cost element exists in actual project and can be safely deleted:
  ```python
  actual_ce = line_item.actual_target_cost_element
  # Check if cost element has cost registrations, earned value entries, etc.
  ```
- Preview shows: "Will delete Cost Element [CE-002]: Procurement (budget: -20000.00, revenue: -22000.00)"
- **No actual project impact:** Actual cost element still exists

**Execution Phase:**
- System compares staging project vs actual project
- Detects cost element exists in actual but not in staging (deleted from staging)
- Deletes cost element from actual project:
  ```python
  actual_ce = session.get(CostElement, line_item.actual_target_cost_element_id)
  # actual_ce.department_name = "Procurement"
  session.delete(actual_ce)
  session.commit()
  ```
- **Foreign key relationship preserved:** Line item `actual_target_cost_element_id` still contains cost element UUID (historical record)
- **Project impact:** Cost element deleted from actual project

---

### Example 7: FINANCIAL_ADJUSTMENT Operation (Staging Project Approach)

**Scenario:** Adjust budget and revenue for existing cost element without structural changes.

**Staging Project Setup:**
- Staging project created with copy of actual project
- Actual Cost Element ID: "440e8400-e29b-41d4-a716-446655440002" (budget: 60000.00, revenue: 70000.00)
- Staging Cost Element ID: "cc0e8400-e29b-41d4-a716-446655440002" (copy of actual)

**Design Phase:**
- User modifies cost element financial attributes in staging project:
  ```python
  # Staging cost element updated
  staging_ce.budget_bac = 70000.00  # Increased by €10,000
  staging_ce.revenue_plan = 82000.00  # Increased by €12,000
  ```
- System automatically creates/updates line item:
  ```python
  ChangeOrderLineItem(
      change_order_line_id: "550e8400-e29b-41d4-a716-446655440007",
      change_order_id: "550e8400-e29b-41d4-a716-446655440000",
      operation_type: "financial_adjustment",
      target_type: "cost_element",
      staging_target_cost_element_id: "cc0e8400-e29b-41d4-a716-446655440002",  # FK to staging
      actual_target_cost_element_id: "440e8400-e29b-41d4-a716-446655440002",  # FK to actual
      budget_change: 10000.00,  # Calculated: staging (70000) - actual (60000)
      revenue_change: 12000.00,  # Calculated: staging (82000) - actual (70000)
      description: "Financial adjustment due to material cost increase",
      sequence_number: 7
  )
  ```
- **Foreign key relationships exist:** Both staging and actual cost elements referenced
- System can load both via relationships:
  ```python
  staging_ce = line_item.staging_target_cost_element
  # staging_ce.budget_bac = 70000.00, revenue_plan = 82000.00
  actual_ce = line_item.actual_target_cost_element
  # actual_ce.budget_bac = 60000.00, revenue_plan = 70000.00
  ```
- Preview shows: "Will adjust Cost Element [CE-003]: budget 60000.00 → 70000.00, revenue 70000.00 → 82000.00"
- **No actual project impact:** Actual cost element unchanged, only staging modified

**Execution Phase:**
- System compares staging cost element vs actual cost element
- Detects financial differences: budget and revenue changed
- Applies financial changes from staging to actual:
  ```python
  actual_ce = session.get(CostElement, line_item.actual_target_cost_element_id)
  staging_ce = session.get(CostElement, line_item.staging_target_cost_element_id)
  actual_ce.budget_bac = staging_ce.budget_bac
  actual_ce.revenue_plan = staging_ce.revenue_plan
  # actual_ce.budget_bac = 70000.00 (after)
  # actual_ce.revenue_plan = 82000.00 (after)
  ```
- Updates actual cost element in database
- **Foreign key relationships maintained:** Both references preserved
- **Project impact:** Only financial attributes updated in actual project

---

## Summary: Relationship Patterns (Staging Project Approach)

| Operation | Staging Relationship | Actual Relationship | staging_target_id | actual_target_id | After Execution |
|-----------|---------------------|---------------------|-------------------|------------------|-----------------|
| CREATE WBE | FK → WBE in staging | None | NOT NULL | NULL | Staging FK preserved (historical) |
| CREATE Cost Element | FK → CostElement in staging | None | NOT NULL | NULL | Staging FK preserved (historical) |
| UPDATE WBE | FK → WBE in staging | FK → WBE in actual | NOT NULL | NOT NULL | Both FKs maintained |
| UPDATE Cost Element | FK → CostElement in staging | FK → CostElement in actual | NOT NULL | NOT NULL | Both FKs maintained |
| DELETE WBE | None (deleted from staging) | FK → WBE in actual | NULL | NOT NULL | Actual FK preserved (historical) |
| DELETE Cost Element | None (deleted from staging) | FK → CostElement in actual | NULL | NOT NULL | Actual FK preserved (historical) |
| FINANCIAL_ADJUSTMENT | FK → CostElement in staging | FK → CostElement in actual | NOT NULL | NOT NULL | Both FKs maintained |

**Key Benefits of Staging Project Approach:**
1. **Simpler relationships:** All elements use standard foreign keys (no conditional logic)
2. **Direct modification:** Users work with real project structure (staging project)
3. **Better validation:** Can validate staging project using existing validation rules
4. **Easier comparison:** Compare staging vs actual project directly
5. **Cleaner execution:** Copy/sync elements from staging to actual (simpler than parsing JSON)
6. **No JSON storage:** All elements stored in database using existing models
7. **Better user experience:** Users work with familiar project structure interface

**Key Insights:**
1. **CREATE operations** have no relationship (target doesn't exist)
2. **UPDATE/DELETE operations** have direct FK relationships via `target_id`
3. **FINANCIAL_ADJUSTMENT** uses separate `cost_element_id` field
4. **After execution**, CREATE operations don't create backward relationships (by design)
5. **Historical records** are preserved even after DELETE operations

**Line Item Processing Logic:**

**Design Phase (Status: "design"):**
1. **Storage Only:** Line items are stored but not processed
2. **Validation:** Validate line item structure
   - For update/delete: Validate `target_id` exists and matches `target_type`
   - For create: Validate required fields in `new_wbe_data` or `new_cost_element_data`
   - For financial_adjustment: Validate `cost_element_id` exists
   - Validate required fields present
3. **Preview Generation:** Generate preview of changes without applying them
   - Load existing elements referenced by `target_id` or `cost_element_id`
   - Simulate create operations from stored data
4. **No Project Impact:** Project data remains unchanged
5. **No Relationship Validation:** Foreign key relationships not enforced (targets may not exist for create operations)

**Approval Request (Status: "design" → "approve"):**
1. **Baseline Creation:** Create "before" baseline snapshot of current project state
2. **Comprehensive Validation:** Validate all line items and their relationships
   - **UPDATE/DELETE Operations:**
     - Ensure `target_id` exists in database
     - Verify `target_type` matches actual element type
     - Load and validate target element exists and is accessible
   - **CREATE Operations:**
     - Validate `new_wbe_data` or `new_cost_element_data` contains required fields
     - Check for conflicts (e.g., duplicate machine_type, overlapping identifiers)
     - Validate new element won't violate project constraints
   - **FINANCIAL_ADJUSTMENT Operations:**
     - Ensure `cost_element_id` exists in database
     - Load and validate cost element exists
   - Check financial constraints (budget limits, revenue limits)
   - Validate sequence numbers are unique and sequential
3. **Lock Changes:** Change order becomes read-only (cannot edit line items)
4. **No Project Impact:** Changes still NOT applied to project
5. **Relationship Preservation:** All foreign key relationships validated and preserved

**Approval Completion (Status: "approve" → "execute"):**
1. **Apply Changes:** Process line items in sequence_number order
   - **CREATE Operations:**
     - Create new WBE or cost element from `new_wbe_data` or `new_cost_element_data`
     - New element receives UUID, but line item `target_id` remains NULL (historical record)
     - No foreign key relationship created (element didn't exist when line item was created)
   - **UPDATE Operations:**
     - Load existing element via `target_id` foreign key relationship
     - Apply modifications (budget_change, revenue_change, or other attributes)
     - Update element in database
     - Foreign key relationship maintained
   - **DELETE Operations:**
     - Load existing element via `target_id` foreign key relationship
     - Delete element from database
     - Line item preserves `target_id` reference (historical record, may become invalid)
   - **FINANCIAL_ADJUSTMENT Operations:**
     - Load existing cost element via `cost_element_id` foreign key relationship
     - Apply budget_change and revenue_change
     - Update element financial attributes
     - Foreign key relationship maintained
2. **Transaction Safety:** All operations in a single database transaction
3. **Rollback:** If any operation fails, rollback entire transaction
4. **Baseline Creation:** Create "after" baseline snapshot of new project state
5. **Project Impact:** Changes are now applied to live project data
6. **EVM Recalculation:** Trigger recalculation of EVM metrics for affected elements
7. **Relationship Updates:**
   - New elements created have no backward relationship to line items (by design)
   - Updated/deleted elements maintain historical relationship via line item `target_id`

### User Stories for Project Element Modifications

**As a** project manager
**I want to** create a change order that adds a new WBE to the project
**So that** I can document when a customer requests an additional machine, track the financial impact, and ensure the new WBE is properly integrated into the project structure with appropriate budget and revenue allocations.

**As a** project manager
**I want to** create a change order that modifies multiple cost elements simultaneously
**So that** I can document scope adjustments affecting multiple departments in a single change order, ensuring all related changes are tracked together and approved as a cohesive unit.

**As a** project manager
**I want to** see a preview of how the project structure will change before approving a change order
**So that** I can verify that all intended modifications are correctly specified and understand the full impact on project hierarchy and finances.

**As a** project controller
**I want to** compare the project structure before and after a change order execution
**So that** I can generate reports showing exactly what changed, analyze the impact on project metrics, and provide stakeholders with clear documentation of scope modifications.

**As a** project manager
**I want to** see a visual diff showing which WBEs and cost elements were added, modified, or removed by a change order
**So that** I can quickly understand the scope of changes without manually comparing baseline snapshots.

**As a** finance manager
**I want to** review change orders that delete project elements with confirmation of financial impact
**So that** I can ensure that budget and revenue adjustments are properly calculated and that deleted elements don't have outstanding commitments.

**As a** project manager
**I want to** create change orders that combine structural changes (create/update/delete) with financial adjustments
**So that** I can document complex scope changes that involve both adding new work and adjusting existing budgets in a single change order.

**As a** project controller
**I want to** see a timeline of all change orders and their impact on project structure
**So that** I can track how the project has evolved over time, identify trends in scope changes, and analyze the cumulative impact of multiple change orders.

**As a** project manager
**I want to** design change orders with multiple modifications without affecting the live project
**So that** I can iterate on the change order design, preview the impact, and refine the changes before requesting approval, without disrupting ongoing project work.

**As a** project manager
**I want to** preview how the project structure will change before requesting approval
**So that** I can verify all modifications are correct, understand the full scope of changes, and catch any errors before the change order enters the approval workflow.

**As a** project controller
**I want to** see that change orders in "design" status do not affect project data
**So that** I can ensure project integrity and that only approved changes impact the live project structure and financials.

---

## Requirements Summary

**From PRD (Section 8.1 - 8.3):**
- System shall provide comprehensive change order management capabilities
- Each change order must have: unique identifier, description, requesting party, justification, proposed effective date
- Change orders must support modifications to both costs and revenues
- System must maintain original baseline data while tracking impact of approved changes
- System shall track change order status through workflow states: draft, submitted, under_review, approved, rejected, implemented
- Each status transition must be recorded with timestamp and responsible user information
- System shall provide impact analysis showing effect on budgets, WBE allocations, cost element budgets, revenue recognition, schedule implications, and EVM performance indices

**From Data Model:**
- ChangeOrder model exists with all required fields
- Status enum: **design, approve, execute** (extensible for future statuses)
- Optional WBE association (NULL if project-wide)
- **Change Order Line Item model does NOT exist - must be created**
- Line items can target cost elements for budget/revenue changes
- Line items can also specify WBE/cost element creation, update, or deletion operations
- Relationships: Belongs to Project, optional WBE, created_by/approved_by/implemented_by Users

**From Plan.md (Sprint 6):**
- Change Order Entry Interface is Sprint 6 deliverable
- Must document scope changes and financial impacts
- Tracks change orders through workflow
- E5-004 (Change Order Workflow) handles status tracking implementation
- E5-005 (Budget Adjustment Logic) handles automatic budget/revenue updates on approval

**Stakeholder Clarifications Received (2025-11-23):**
- ✅ **Change Order Line Item Model:** Does not exist, must be created as part of E5-003
- ✅ **Workflow Statuses:** Start with 'design' → 'approve' → 'execute', but system must allow adding new statuses in the future (extensible enum)
- ✅ **Change Order Number:** Auto-generated format: 'CO' + project ID (shortened) + progressive number (e.g., "CO-PRJ001-001", "CO-PRJ001-002")
- ✅ **Financial Impact:** Calculated automatically from line items (sum of budget_change and revenue_change)
- ✅ **Line Items:** Required for all change orders (cannot create change order without at least one line item)
- ✅ **Project Element Modifications:** Change orders can create, update, or delete multiple WBEs and cost elements
- ✅ **Baselining for Change Tracking:** When change order is approved/executed, system must create baseline snapshots to record "before" and "after" state, enabling comparison of how project structure changed

---

## 1. CODEBASE PATTERN ANALYSIS

### 1.1 Existing Change Order Model

**Location:** `backend/app/models/change_order.py`

**Current State:**
- ✅ Model exists with all required fields: `change_order_id`, `project_id`, `wbe_id`, `change_order_number`, `title`, `description`, `requesting_party`, `justification`, `effective_date`, `cost_impact`, `revenue_impact`, `status`
- ✅ Base/Create/Update/Public schema pattern implemented
- ✅ Relationships to Project, WBE (optional), User (created_by, approved_by, implemented_by)
- ✅ Tests exist: `backend/tests/models/test_change_order.py` (3 tests passing)
- ❌ **Missing:** API routes for CRUD operations
- ❌ **Missing:** Status enum validation (currently string field) - **Update to: design, approve, execute (extensible)**
- ❌ **Missing:** Change Order Line Item model implementation - **MUST BE CREATED**
- ❌ **Missing:** Line item support for WBE/cost element create/update/delete operations
- ❌ **Missing:** Baseline snapshot creation on change order approval/execution
- ❌ **Missing:** Before/after state comparison functionality
- ❌ **Missing:** Change order number auto-generation logic
- ❌ **Missing:** Frontend components
- ❌ **Missing:** Workflow transition logic

**Schema Structure (Current):**
```python
class ChangeOrderBase:
    change_order_number: str (unique, max 50)
    title: str (max 200)
    description: str
    requesting_party: str (max 100)
    justification: str | None
    effective_date: date
    cost_impact: Decimal | None
    revenue_impact: Decimal | None
    status: str (max 50)  # Enum validation needed

class ChangeOrder (table):
    change_order_id: UUID (PK)
    project_id: UUID (FK → Project)
    wbe_id: UUID | None (FK → WBE)
    created_by_id: UUID (FK → User)
    approved_by_id: UUID | None (FK → User)
    approved_at: datetime | None
    implemented_by_id: UUID | None (FK → User)
    implemented_at: datetime | None
    created_at: datetime
```

### 1.2 Similar CRUD Pattern: Forecast Interface (E5-001)

**Location:** `frontend/src/components/Projects/ForecastsTable.tsx`, `AddForecast.tsx`, `EditForecast.tsx`

**Pattern Analysis:**
- ✅ Tab-based interface in cost element detail page
- ✅ DataTable component with Add/Edit/Delete actions
- ✅ Dialog-based forms (Add/Edit) with React Hook Form
- ✅ Validation hooks for business rules
- ✅ Status indicators (current forecast badge)
- ✅ Query invalidation on CRUD operations
- ✅ Empty state handling
- ✅ User mapping for display names

**Reusable Components:**
- `DataTable` component (TanStack Table v8)
- Dialog components (`DialogRoot`, `DialogContent`, `DialogHeader`, `DialogBody`)
- Form field components (`Field`, `Input`, `Select`, `Textarea`)
- Validation hooks pattern (`useForecastDateValidation`, `useEACValidation`)

### 1.3 Similar Workflow Pattern: Baseline Log (E3-005)

**Location:** `backend/app/api/routes/baseline_logs.py`, `frontend/src/components/Projects/BaselineLogsTable.tsx`

**Pattern Analysis:**
- ✅ Project-scoped CRUD API
- ✅ Status tracking with timestamps
- ✅ User attribution (created_by, approved_by)
- ✅ Soft delete via `is_cancelled` flag
- ✅ Tab integration in project detail page
- ✅ Status badge display in table

**Reusable Patterns:**
- Project-scoped API route structure
- Status enum validation helper functions
- User relationship handling
- Timestamp tracking for workflow transitions

### 1.4 Similar Financial Impact Pattern: Budget Allocation (E2-001)

**Location:** `backend/app/models/budget_allocation.py`, `backend/app/api/routes/budget_allocations.py`

**Pattern Analysis:**
- ✅ Cost element-level financial tracking
- ✅ Validation for budget limits
- ✅ Allocation type enum (initial, change_order, adjustment)
- ✅ Related change order reference (commented out, ready for implementation)

**Reusable Patterns:**
- Financial validation helpers
- Allocation type tracking
- Change order linkage pattern

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### 2.1 Backend Integration Points

**New API Routes Required:**
- `backend/app/api/routes/change_orders.py` (new file)
  - GET `/api/v1/projects/{project_id}/change-orders` - List change orders
  - GET `/api/v1/projects/{project_id}/change-orders/{change_order_id}` - Read change order
  - POST `/api/v1/projects/{project_id}/change-orders` - Create change order
  - PUT `/api/v1/projects/{project_id}/change-orders/{change_order_id}` - Update change order
  - DELETE `/api/v1/projects/{project_id}/change-orders/{change_order_id}` - Delete change order (soft delete or hard delete?)
  - POST `/api/v1/projects/{project_id}/change-orders/{change_order_id}/transition` - Status transition (draft → submitted, etc.)

**Model Updates:**
- `backend/app/models/change_order.py` - Add status enum validation (design, approve, execute - extensible)
- `backend/app/models/project.py` - Add `is_staging`, `staging_for_change_order_id`, `staging_for_project_id` fields
- `backend/app/models/change_order_line_item.py` - **CREATE NEW MODEL** with staging_target_id and actual_target_id fields
- `backend/app/models/__init__.py` - Export new models
- Update ChangeOrder model to support auto-generated change_order_number

**Helper Functions:**
- `backend/app/api/routes/change_orders.py` - Status enum validation (design, approve, execute - extensible)
- `backend/app/api/routes/change_orders.py` - Workflow transition validation (design → approve → execute)
- `backend/app/api/routes/change_orders.py` - Financial impact calculation (sum of line items budget_change and revenue_change)
- `backend/app/api/routes/change_orders.py` - Change order number auto-generation ('CO' + project_id_short + progressive_number)
- `backend/app/api/routes/change_orders.py` - **Baseline snapshot creation on approval request** (before baseline when design → approve)
- `backend/app/api/routes/change_orders.py` - **Baseline snapshot creation on approval completion** (after baseline when approve → execute)
- `backend/app/api/routes/change_orders.py` - **Staging project creation** (copy actual project to staging on change order creation)
- `backend/app/api/routes/change_orders.py` - **Staging project comparison** (compare staging vs actual project, generate line items)
- `backend/app/api/routes/change_orders.py` - **Staging project sync** (apply staging changes to actual project on approve → execute)
- `backend/app/api/routes/change_orders.py` - **Line item auto-generation** (generate line items from staging vs actual comparison)
- `backend/app/api/routes/change_orders.py` - **Change order edit lock** (prevent edits after design phase, lock staging project)

**Router Registration:**
- `backend/app/api/main.py` - Register change_orders router

### 2.2 Frontend Integration Points

**New Components Required:**
- `frontend/src/components/Projects/ChangeOrdersTable.tsx` - Main table component
- `frontend/src/components/Projects/changeOrderColumns.tsx` - Column definitions
- `frontend/src/components/Projects/AddChangeOrder.tsx` - Create dialog (creates staging project automatically)
- `frontend/src/components/Projects/EditChangeOrder.tsx` - Edit dialog (only enabled for "design" status)
- `frontend/src/components/Projects/DeleteChangeOrder.tsx` - Delete confirmation (only enabled for "design" status, deletes staging project)
- `frontend/src/components/Projects/ChangeOrderStagingProjectView.tsx` - **Staging project view** (shows staging project structure, allows modifications)
- `frontend/src/components/Projects/ChangeOrderComparisonView.tsx` - **Comparison view** (side-by-side staging vs actual project)
- `frontend/src/components/Projects/ChangeOrderLineItemsTable.tsx` - Line items table (auto-generated from staging project changes)
- `frontend/src/components/Projects/ChangeOrderStatusTransition.tsx` - Status transition dialog

**Page Integration:**
- `frontend/src/routes/_layout/projects.$id.tsx` - Add "Change Orders" tab to project detail page
- `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.tsx` - Optional: Add change orders view to WBE detail page

**Hooks:**
- `frontend/src/hooks/useChangeOrderStatusValidation.ts` - Status transition validation
- `frontend/src/hooks/useChangeOrderImpactCalculation.ts` - Financial impact calculation

**API Client:**
- Regenerate OpenAPI client after backend API implementation

### 2.3 Database Schema

**Existing Tables:**
- `changeorder` table exists with all required columns
- `changeorderlineitem` table may need to be created (check data model)

**Migrations:**
- May need migration for status enum constraint (if using database-level enum)
- May need migration for change order line item table (if not exists)

### 2.4 External Dependencies

**Time Machine Support:**
- Change orders must respect control date filtering
- Only show change orders created/modified on or before control date
- Impact calculations must use control date for baseline comparisons

**EVM Integration:**
- Change orders affect budget allocations (E5-005)
- Change orders affect revenue allocations
- Change orders may affect planned value calculations (if schedule changes)
- Change orders must be considered in variance analysis

---

## 3. ABSTRACTION INVENTORY

### 3.1 Reusable Backend Abstractions

**Status Enum Validation:**
- Pattern from `baseline_logs.py`: `validate_milestone_type()` function
- Can create: `validate_change_order_status()` function
- Status enum: `["draft", "submitted", "under_review", "approved", "rejected", "implemented"]`

**Workflow Transition Logic:**
- Pattern from baseline logs: Status transitions with user attribution
- Can create: `transition_change_order_status()` function
- Validates allowed transitions (e.g., draft → submitted, submitted → under_review, etc.)
- Records timestamp and user for each transition

**Financial Validation:**
- Pattern from `budget_allocations.py`: Budget limit validation
- Can reuse: Budget and revenue validation helpers
- Can create: Change order impact validation (warn if exceeds project budget/revenue)

**Project-Scoped CRUD:**
- Pattern from `baseline_logs.py`: Project-scoped API routes
- Can reuse: `project_id` parameter validation
- Can reuse: Project existence validation

### 3.2 Reusable Frontend Abstractions

**DataTable Component:**
- Location: `frontend/src/components/DataTable/DataTable.tsx`
- Reusable for: Change orders table, line items table
- Features: Sorting, filtering, pagination, column visibility

**Dialog Components:**
- Location: Chakra UI Dialog components
- Reusable for: Add/Edit/Delete change order dialogs
- Pattern: `DialogRoot`, `DialogContent`, `DialogHeader`, `DialogBody`, `DialogFooter`

**Form Validation Hooks:**
- Pattern: `useForecastDateValidation`, `useEACValidation`
- Can create: `useChangeOrderStatusValidation`, `useChangeOrderImpactCalculation`
- Reusable: React Hook Form integration

**Status Badge Component:**
- Pattern: Status indicators in ForecastsTable, BaselineLogsTable
- Can reuse: Color-coded status badges
- Status colors: draft (gray), submitted (blue), under_review (yellow), approved (green), rejected (red), implemented (purple)

**User Display Mapping:**
- Pattern: User ID to name mapping in ForecastsTable
- Can reuse: `useQuery` for users list, `useMemo` for user map

### 3.3 Test Utilities

**Backend Test Fixtures:**
- Pattern: `test_change_order.py` - Change order creation fixtures
- Can reuse: Project, User, WBE creation helpers
- Can create: Change order line item fixtures

**Frontend Test Utilities:**
- Pattern: E2E tests for Forecast CRUD (`forecast-crud.spec.ts`)
- Can reuse: Dialog interaction patterns, form filling patterns
- Can create: Change order workflow E2E tests

---

## 4. ALTERNATIVE APPROACHES

### Approach 1: Incremental Enhancement (Recommended)

**Description:** Build change order CRUD interface following Forecast pattern, then add workflow and line items in subsequent phases.

**Implementation Phases:**
1. **Phase 1:** Basic CRUD (Create, Read, Update, Delete) for change orders
   - Simple form with all change order fields
   - Status dropdown (editable in draft only)
   - Project-scoped table view
   - Tab integration in project detail page

2. **Phase 2:** Workflow transitions (E5-004 integration)
   - Status transition API endpoints
   - Workflow validation (allowed transitions)
   - User attribution for approvals
   - Status badge display

3. **Phase 3:** Change order line items
   - Line items table (nested in change order detail)
   - Add/Edit/Delete line items
   - Automatic cost/revenue impact calculation from line items
   - Cost element selection for line items

4. **Phase 4:** Impact analysis (E5-005 integration)
   - Budget/revenue adjustment on approval
   - Impact visualization
   - Baseline preservation

**Pros:**
- ✅ Follows established patterns (Forecast, Baseline Log)
- ✅ Incremental delivery enables early testing
- ✅ Lower risk - each phase builds on previous
- ✅ Aligns with existing architecture
- ✅ Reuses existing abstractions

**Cons:**
- ⚠️ Requires multiple phases
- ⚠️ Line items deferred to Phase 3 (may limit initial functionality)

**Estimated Complexity:** Medium (4 phases, 20-30 hours total)

**Risk Factors:**
- Low risk - follows proven patterns
- Dependency on E5-004 and E5-005 for full functionality

### Approach 2: Comprehensive Single Phase

**Description:** Implement complete change order interface with CRUD, workflow, line items, and impact analysis in one phase.

**Implementation:**
- All features in single implementation
- Complete API with all endpoints
- Full frontend with all components
- Comprehensive test coverage

**Pros:**
- ✅ Complete functionality delivered at once
- ✅ No intermediate states
- ✅ Full feature set available immediately

**Cons:**
- ❌ Higher complexity and risk
- ❌ Longer development time (40-50 hours)
- ❌ More difficult to test incrementally
- ❌ May delay delivery if issues arise

**Estimated Complexity:** High (single phase, 40-50 hours)

**Risk Factors:**
- Higher risk - more moving parts
- Potential for scope creep
- Difficult to validate incrementally

### Approach 3: Wizard-Based Creation (Post-MVP Enhancement)

**Description:** Multi-step wizard for change order creation (similar to E5-001A Forecast Wizard).

**Implementation:**
- Step 1: Basic information (title, description, requesting party)
- Step 2: Financial impacts (cost/revenue impacts or line items)
- Step 3: Justification and effective date
- Step 4: Review and confirmation

**Pros:**
- ✅ Improved UX for complex change orders
- ✅ Guided workflow reduces errors
- ✅ Better for users unfamiliar with change order process

**Cons:**
- ❌ Additional complexity
- ❌ Not required for MVP
- ❌ Can be added as enhancement (E5-003A)

**Estimated Complexity:** Medium-High (enhancement, 15-20 hours)

**Risk Factors:**
- Low risk - post-MVP enhancement
- Can be deferred to future sprint

**Recommendation:** Approach 1 (Incremental Enhancement) - Follows established patterns, enables incremental delivery, lower risk, aligns with TDD discipline and working agreements.

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### 5.1 Architectural Principles

**Follows:**
- ✅ **Separation of Concerns:** Backend API, frontend components, shared models
- ✅ **DRY (Don't Repeat Yourself):** Reuses existing patterns (Forecast, Baseline Log)
- ✅ **Single Responsibility:** Each component has clear purpose
- ✅ **Consistency:** Follows established CRUD patterns
- ✅ **Testability:** TDD approach with comprehensive test coverage

**Potential Violations:**
- ⚠️ **Complexity:** Change order line items add nested CRUD complexity
  - **Mitigation:** Separate line items into dedicated components, reuse table patterns

### 5.2 Maintenance Considerations

**Future Maintenance Burden:**
- **Workflow Rules:** Status transition rules may need updates as business processes evolve
  - **Mitigation:** Centralize workflow rules in configuration or helper functions
- **Impact Calculations:** Financial impact calculations may need refinement
  - **Mitigation:** Separate calculation logic into service layer for easy updates
- **Line Items Complexity:** Nested line items add UI complexity
  - **Mitigation:** Use collapsible sections, clear visual hierarchy

**Code Duplication Risks:**
- **Low Risk:** Following established patterns minimizes duplication
- **Potential Areas:** Status badge logic, form validation patterns
  - **Mitigation:** Extract shared status badge component, reuse validation hooks

### 5.3 Testing Challenges

**Backend Testing:**
- **Workflow Transitions:** Need to test all valid/invalid status transitions
  - **Approach:** Comprehensive test matrix for status transitions
- **Financial Impact:** Need to test impact calculations from line items
  - **Approach:** Unit tests for calculation logic, integration tests for API
- **User Attribution:** Need to test approval/implementation user tracking
  - **Approach:** Test user relationship updates on status transitions

**Frontend Testing:**
- **Workflow UI:** Need to test status transition buttons and validation
  - **Approach:** E2E tests for workflow transitions
- **Line Items:** Need to test nested CRUD operations
  - **Approach:** Component tests for line items table, E2E tests for full workflow
- **Form Validation:** Need to test all validation rules
  - **Approach:** Unit tests for validation hooks, E2E tests for form submission

**Integration Testing:**
- **E5-005 Integration:** Change orders must integrate with budget adjustment logic
  - **Approach:** Integration tests for approved change order → budget update flow
- **Time Machine:** Change orders must respect control date
  - **Approach:** Tests for control date filtering, impact calculations at different dates

### 5.4 Performance Considerations

**Database Queries:**
- **Change Orders List:** May need pagination for projects with many change orders
  - **Mitigation:** Implement pagination in API (skip/limit parameters)
- **Line Items:** Nested queries for line items per change order
  - **Mitigation:** Use eager loading or separate endpoint for line items

**Frontend Performance:**
- **Large Tables:** Change orders table may grow large
  - **Mitigation:** Use DataTable pagination, virtual scrolling if needed
- **Line Items Rendering:** Many line items may impact render performance
  - **Mitigation:** Virtual scrolling, lazy loading, collapsible sections

### 5.5 Security Considerations

**Access Control:**
- **Role-Based Permissions:** Who can create/approve/implement change orders?
  - **Requirement:** Define role permissions (project manager, finance manager, executive)
  - **Mitigation:** Implement role checks in API routes

**Data Validation:**
- **Status Transitions:** Prevent unauthorized status changes
  - **Requirement:** Validate user permissions for each transition
  - **Mitigation:** Role-based transition validation

**Financial Integrity:**
- **Impact Validation:** Prevent invalid financial impacts
  - **Requirement:** Validate cost/revenue impacts against project limits
  - **Mitigation:** Backend validation, frontend warnings

---

## 6. USER INTERFACE DESIGN (PMP Standards)

### 6.1 Change Orders Tab in Project Detail Page

**Location:** Project Detail Page (`/projects/:id`)

**Experience Flow:**
1. **Navigation:** User navigates to project detail page
2. **Tab Selection:** User sees "Change Orders" tab alongside existing tabs (Summary, WBEs, Baselines, etc.)
3. **Tab Content:** Upon selecting "Change Orders" tab, user sees:
   - Change orders table showing all change orders for the project
   - "Add Change Order" button in table header (right-aligned)
   - Table displays: Change Order Number, Title, Status, Requesting Party, Effective Date, Cost Impact, Revenue Impact, Created By, Created Date, Actions (View/Edit/Delete/Transition)
   - Table sorted by `created_at` descending (newest first) by default
   - Optional filtering by status, requesting party, date range
   - Optional sorting by any column

**Visual Design:**
- Follows Chakra UI design system consistent with existing tabs
- Table uses DataTable component (matches ForecastsTable, BaselineLogsTable pattern)
- Status badges with color coding:
  - Draft: Gray
  - Submitted: Blue
  - Under Review: Yellow
  - Approved: Green
  - Rejected: Red
  - Implemented: Purple
- Empty state: "No change orders created yet. Click 'Add Change Order' to create your first change order."
- Responsive design: Table scrolls horizontally on mobile, maintains column visibility toggle

### 6.2 Add Change Order Dialog

**Trigger:** Click "Add Change Order" button in Change Orders tab

**Dialog Experience:**

1. **Dialog Opens:** Modal dialog appears (size: `lg` - matches AddForecast pattern)

2. **Form Fields (in order):**
   - **Change Order Number** (auto-generated, read-only display)
     - Format: "CO-[PROJECT_ID_SHORT]-[PROGRESSIVE_NUMBER]" (e.g., "CO-PRJ001-001", "CO-PRJ001-002")
     - Auto-generated on change order creation
     - Display only (not editable)
     - Help text: "Automatically generated unique identifier for this change order"

   - **Title** (required, text input, max 200 chars)
     - Placeholder: "Brief title describing the change"
     - Validation: Required, max length 200
     - Help text: "Short descriptive title for the change order"

   - **Description** (required, textarea)
     - Placeholder: "Detailed description of the scope change..."
     - Validation: Required
     - Help text: "Comprehensive description of what is changing and why"

   - **Requesting Party** (required, select dropdown)
     - Options: "Customer", "Internal", "Subcontractor", "Other"
     - Default: "Customer"
     - Help text: "Who requested this change"

   - **WBE** (optional, select dropdown)
     - Options: All WBEs for the project
     - Default: None (project-wide change order)
     - Help text: "Select specific WBE if change applies to one machine, or leave blank for project-wide change"

   - **Effective Date** (required, date picker)
     - Default: Today's date
     - Validation: Required
     - Help text: "Proposed or actual date when this change becomes effective"

   - **Justification** (optional, textarea)
     - Placeholder: "Business case and rationale for this change..."
     - Help text: "Optional: Explain why this change is necessary"

   - **Status** (required, select dropdown, default: "design")
     - Options: "Design", "Approve", "Execute"
     - Default: "Design"
     - Help text: "Initial status for this change order. Use workflow transitions to change status."
     - Note: Status can only be changed via workflow transitions after creation
     - Note: System is extensible to add new statuses in the future

   - **Cost Impact** (auto-calculated, read-only display)
     - Calculated automatically: Sum of `budget_change` from all line items
     - Display: Currency format (e.g., "€50,000.00")
     - Updates automatically when line items are added/modified/deleted
     - Help text: "Total cost impact calculated from all line items"

   - **Revenue Impact** (auto-calculated, read-only display)
     - Calculated automatically: Sum of `revenue_change` from all line items
     - Display: Currency format (e.g., "€60,000.00")
     - Updates automatically when line items are added/modified/deleted
     - Help text: "Total revenue impact calculated from all line items"

   - **Line Items** (required, nested table)
     - Minimum: At least 1 line item required to create change order
     - Table showing: Operation Type, Target Type, Target Element, Budget Change, Revenue Change, Description, Actions
     - "Add Line Item" button opens dialog for creating line items
     - Line items can specify: create/update/delete operations for WBEs and cost elements
     - Line items can specify: financial adjustments to existing cost elements
     - Validation: At least one line item must be present before submission

3. **Form Validation:**
   - Real-time validation on blur (matches existing patterns)
   - Error messages displayed inline below fields
   - Submit button disabled until all required fields valid
   - Change order number uniqueness validation (async check)

4. **Submission:**
   - Click "Create Change Order" button (primary button, bottom right)
   - Loading state: Button shows spinner, form disabled during submission
   - Success: Dialog closes, success toast: "Change order created successfully"
   - Error: Error toast with detailed message, form remains open
   - Query invalidation: Change orders table refreshes

### 6.3 Edit Change Order Dialog

**Trigger:** Click "Edit" action button in Change Orders table row (only enabled for "design" status)

**Dialog Experience:**

1. **Dialog Opens:** Modal dialog pre-populated with existing change order data

2. **Form Fields:** Same as Add Change Order, but:
   - All fields pre-filled with current values
   - Status field disabled (status changes via workflow transitions only)
   - Warning shown if status is not "design": "Only change orders in 'design' status can be edited. Use workflow transitions to change status."
   - Form title: "Edit Change Order" (vs "Add Change Order")
   - **Line items section:** Fully editable (add/edit/delete line items)
   - **Preview button:** Shows preview of changes without applying them

3. **Validation:** Same as Add Change Order

4. **Submission:**
   - Click "Update Change Order" button
   - Success toast: "Change order updated successfully"
   - **Note:** Changes are stored but NOT applied to project (staged only)
   - Query invalidation: Table refreshes

### 6.4 Change Order Detail View

**Trigger:** Click "View" action button in Change Orders table row

**Modal/Page Experience:**
- Full change order details with read-only view (if status is "approve" or "execute")
- Line items table showing all modifications
- **Preview Changes Section:** Shows how project structure will change (for "design" status)
- **Before/After Comparison:** Shows baseline snapshots comparison (for "execute" status)
- Workflow history (status transitions with timestamps and users)
- Impact analysis summary (financial impacts calculated from line items)
- Actions:
  - Edit (only if "design" status)
  - Preview Changes (only if "design" status)
  - Transition Status (design → approve, approve → execute)
  - Delete (only if "design" status)

### 6.5 Status Transition Dialog

**Trigger:** Click "Transition Status" action button in Change Orders table row

**Dialog Experience:**

**Transition: design → approve (Approval Request)**
1. **Dialog Opens:** Modal dialog with confirmation
2. **Current Status Display:** Shows "Design" status with badge
3. **Warning Message:**
   - "This will create a baseline snapshot of the current project state and lock the change order for editing."
   - "Changes will NOT be applied to the project until approval is completed."
4. **Preview Link:** Link to preview changes that will be applied
5. **User Attribution:** Shows "Requested By" field (current user auto-filled)
6. **Comments:** Optional textarea for approval request comments
7. **Submission:**
   - Click "Request Approval" button
   - System creates "before" baseline snapshot
   - Change order becomes read-only (cannot edit)
   - Success toast: "Change order approval requested. Baseline snapshot created."
   - Query invalidation: Table refreshes, status badge updates to "Approve"

**Transition: approve → execute (Approval Completion)**
1. **Dialog Opens:** Modal dialog with confirmation
2. **Current Status Display:** Shows "Approve" status with badge
3. **Warning Message:**
   - "This will apply all changes to the project structure and create a baseline snapshot of the new state."
   - "This action cannot be undone. All modifications will be permanently applied."
4. **Changes Summary:** List of all modifications that will be applied
5. **User Attribution:** Shows "Approved By" field (current user auto-filled)
6. **Comments:** Optional textarea for approval comments
7. **Submission:**
   - Click "Approve and Execute" button
   - System applies all line item modifications to project
   - System creates "after" baseline snapshot
   - Success toast: "Change order executed. All changes have been applied to the project."
   - Query invalidation: Table refreshes, project structure updates, status badge updates to "Execute"

### 6.6 Delete Change Order Dialog

**Trigger:** Click "Delete" action button in Change Orders table row (only enabled for "design" status)

**Confirmation Dialog:**
1. **Warning Dialog Opens:** Confirmation modal (size: `md`)
2. **Content:**
   - Title: "Delete Change Order?"
   - Message: "Are you sure you want to delete change order [change_order_number] - [title]?"
   - Warning: "This action cannot be undone. All associated line items will also be deleted."
   - Note: "This change order is in 'design' status, so no project data has been affected."
3. **Actions:**
   - "Cancel" button (secondary, left)
   - "Delete Change Order" button (destructive/red, right)
4. **Submission:**
   - Success toast: "Change order deleted successfully"
   - Query invalidation: Table refreshes
   - **Note:** Since changes were only staged, no project data needs to be rolled back

### 6.7 Change Order Preview (Design Phase Only)

**Trigger:** Click "Preview Changes" button in Change Order Edit Dialog or Detail View (only visible for "design" status)

**Preview Experience:**
1. **Preview Modal Opens:** Modal showing simulated project structure
2. **Side-by-Side Comparison:**
   - Left panel: Current project structure (WBEs and cost elements)
   - Right panel: Project structure after changes (simulated)
3. **Visual Indicators:**
   - Green highlight: New elements (to be created)
   - Yellow highlight: Modified elements (to be updated)
   - Red highlight: Deleted elements (to be removed)
   - No highlight: Unchanged elements
4. **Financial Impact Summary:**
   - Total cost impact (sum of budget changes)
   - Total revenue impact (sum of revenue changes)
   - Net impact on project budget
5. **Actions:**
   - "Close" button to return to change order
   - "Edit Change Order" button to modify changes
6. **Note:** Preview does NOT affect actual project data - it's a simulation only

### 6.9 Change Order Line Items (Auto-Generated from Staging Project)

**Location:** Nested table in Change Order Add/Edit Dialog (required section)

**Experience:**
- **Required Section:** "Line Items" section in change order form (cannot be collapsed, always visible)
- **Minimum Requirement:** At least 1 line item required to create change order
- **Table Display:** Operation Type, Target Type, Target Element, Budget Change, Revenue Change, Description, Sequence, Actions
- **Add Line Item Button:** Opens dialog for creating line items
- **Line Item Types:**
  - **Create WBE:** Specify new WBE attributes (machine_type, revenue_allocation, etc.)
  - **Create Cost Element:** Specify new cost element attributes (department, budget_bac, revenue_plan, etc.)
  - **Update WBE:** Select existing WBE, specify changes (revenue_change, status, etc.)
  - **Update Cost Element:** Select existing cost element, specify budget_change and revenue_change
  - **Delete WBE:** Select existing WBE to remove
  - **Delete Cost Element:** Select existing cost element to remove
  - **Financial Adjustment:** Select existing cost element, specify budget_change and revenue_change (no structural change)

**Add Line Item Dialog:**
1. **Operation Type** (required, select): Create, Update, Delete, Financial Adjustment
2. **Target Type** (required, select): WBE or Cost Element
3. **Target Selection:**
   - If Update/Delete: Dropdown to select existing WBE or Cost Element
   - If Create: Form fields for new element attributes
4. **Financial Changes:**
   - Budget Change (number input, can be negative)
   - Revenue Change (number input, can be negative)
5. **Description** (optional, textarea)
6. **Sequence Number** (auto-assigned, editable): Order of operations within change order

**Validation:**
- At least one line item required
- Target must exist for update/delete operations
- Sequence numbers must be unique within change order
- Financial changes must be specified for update/financial adjustment operations
- **Edit Restrictions:** Line items can only be added/edited/deleted when change order status is "design"

**Automatic Calculations:**
- Cost Impact: Sum of all budget_change values (updates in real-time)
- Revenue Impact: Sum of all revenue_change values (updates in real-time)
- **Note:** Calculations are for preview only - no project data is affected until approval completion

**Status-Based Behavior:**
- **Design Status:** Line items fully editable, changes staged only
- **Approve Status:** Line items read-only, changes locked, baseline created
- **Execute Status:** Line items read-only, changes applied to project, baseline created

---

## 7. RISKS AND UNKNOWNS

### 7.1 Technical Risks

**Risk: Change Order Line Item Model Not Implemented**
- **Impact:** Medium - Line items required for detailed financial tracking
- **Mitigation:** Check data model, create model if missing, or defer to Phase 3
- **Status:** Unknown - needs verification

**Risk: Status Workflow Complexity**
- **Impact:** Medium - Workflow rules may be more complex than anticipated
- **Mitigation:** Start with simple workflow, enhance based on feedback
- **Status:** Medium risk

**Risk: Financial Impact Calculation Accuracy**
- **Impact:** High - Incorrect calculations affect project budgets
- **Mitigation:** Comprehensive testing, validation against manual calculations
- **Status:** Medium risk

### 7.2 Business Risks

**Risk: Workflow Rules Not Fully Defined**
- **Impact:** High - Cannot implement status transitions without clear rules
- **Mitigation:** Request stakeholder clarification on workflow rules
- **Status:** High risk - needs clarification

**Risk: Approval Authority Not Defined**
- **Impact:** Medium - Cannot implement approval workflow without role definitions
- **Mitigation:** Request role-based permission definitions
- **Status:** Medium risk - needs clarification

**Risk: Change Order Number Generation Rules**
- **Impact:** Low - Affects user experience but not functionality
- **Mitigation:** Start with manual entry, add auto-generation if needed
- **Status:** Low risk

### 7.3 Integration Risks

**Risk: E5-004 and E5-005 Dependencies**
- **Impact:** Medium - Full functionality requires workflow and budget adjustment
- **Mitigation:** Implement basic CRUD first, integrate workflow and adjustments in subsequent phases
- **Status:** Medium risk - manageable with phased approach

**Risk: Time Machine Integration**
- **Impact:** Low - Change orders must respect control date
- **Mitigation:** Follow existing time machine patterns (Forecast, Baseline Log)
- **Status:** Low risk

### 7.4 Resolved Clarifications

1. ✅ **Change Order Line Item Model:** Must be created as part of E5-003
2. ✅ **Status Workflow:** design → approve → execute (extensible for future statuses)
3. ✅ **Change Order Number:** Auto-generated as 'CO' + project ID (shortened) + progressive number
4. ✅ **Financial Impact:** Calculated automatically from line items (sum of budget_change and revenue_change)
5. ✅ **Line Items:** Required for all change orders (minimum 1 line item)
6. ✅ **Project Element Modifications:** Change orders can create, update, or delete WBEs and cost elements
7. ✅ **Baselining:** System creates baseline snapshots before approval and after execution to track changes

### 7.5 Resolved Design Phase Clarifications

1. ✅ **Edit Restrictions:** Change orders can only be edited in "design" status. Once status transitions to "approve", changes are locked.
2. ✅ **Staged Changes:** All modifications in "design" phase are staged only and do NOT affect project data.
3. ✅ **Baseline Snapshot Timing:**
   - "Before" baseline created when status transitions from "design" to "approve" (approval request)
   - "After" baseline created when status transitions from "approve" to "execute" (approval completion)
4. ✅ **Change Application:** Changes are only applied to project when status transitions from "approve" to "execute".

### 7.6 Remaining Unknowns

1. **Approval Authority:** Who can transition from "design" to "approve"? Role-based permissions?
2. **Execution Authority:** Who can transition from "approve" to "execute"? Role-based permissions?
3. **Rollback Capability:** Can executed change orders be rolled back? What happens to created/modified/deleted elements?
4. **Line Item Sequence:** How are line items processed? Sequential or parallel? Dependency validation?
5. **Conflict Resolution:** What happens if line items conflict (e.g., delete WBE that has cost elements being updated)?
6. **Preview Performance:** How to handle preview generation for large projects with many changes?

---

## 8. ESTIMATED EFFORT

### Phase 1: Basic CRUD (Recommended Starting Point)
- **Backend API:** 8-10 hours
- **Frontend Components:** 6-8 hours
- **Testing:** 4-5 hours
- **Total:** 18-23 hours

### Phase 2: Workflow Transitions (E5-004 Integration)
- **Backend Workflow Logic:** 4-6 hours
- **Frontend Transition UI:** 3-4 hours
- **Testing:** 2-3 hours
- **Total:** 9-13 hours

### Phase 3: Change Order Line Items
- **Backend Line Items API:** 6-8 hours
- **Frontend Line Items UI:** 5-7 hours
- **Testing:** 3-4 hours
- **Total:** 14-19 hours

### Phase 4: Impact Analysis (E5-005 Integration)
- **Backend Impact Calculation:** 4-6 hours
- **Frontend Impact Display:** 3-4 hours
- **Testing:** 2-3 hours
- **Total:** 9-13 hours

### Total Estimated Effort (All Phases)
- **Minimum:** 50 hours
- **Maximum:** 68 hours
- **Recommended:** 60 hours (with buffer)

---

## 9. SUCCESS CRITERIA

### Functional Requirements
- ✅ Users can create change orders with all required fields
- ✅ Users can view all change orders for a project in a table
- ✅ Users can edit change orders in "design" status only
- ✅ Users can delete change orders in "design" status only
- ✅ Users can preview changes without affecting project data (design phase)
- ✅ Changes in "design" phase are staged only and do NOT affect project data
- ✅ Users can transition change order status through workflow (design → approve → execute)
- ✅ System creates "before" baseline when approval is requested (design → approve)
- ✅ System creates "after" baseline when approval is completed (approve → execute)
- ✅ System applies changes to project only when status transitions to "execute"
- ✅ System tracks status transitions with timestamps and user attribution
- ✅ Change orders respect time machine control date
- ✅ Change order line items are required and can be added/edited/deleted (design phase only)
- ✅ Financial impacts are calculated automatically from line items
- ✅ Change orders can create, update, or delete WBEs and cost elements
- ✅ Change orders integrate with budget adjustment logic (applied on execution)

### Non-Functional Requirements
- ✅ UI follows Chakra UI design system
- ✅ Components follow established patterns (Forecast, Baseline Log)
- ✅ Comprehensive test coverage (backend + frontend)
- ✅ Performance: Table loads within 2 seconds for 100+ change orders
- ✅ Responsive design: Works on desktop and tablet
- ✅ Accessibility: Keyboard navigation, screen reader support

---

## 10. NEXT STEPS

1. **Stakeholder Clarification:** Request answers to unknowns (Section 7.4)
2. **Data Model Verification:** Verify ChangeOrderLineItem model existence
3. **Detailed Planning:** Create detailed TDD implementation plan for Phase 1
4. **Implementation:** Begin Phase 1 (Basic CRUD) following TDD discipline
5. **Integration:** Coordinate with E5-004 and E5-005 for workflow and budget adjustments

---

## CONCLUSION

E5-003 (Change Order Entry Interface) is a critical Sprint 6 deliverable that enables proper change control and financial impact tracking. The recommended incremental enhancement approach (Approach 1) follows established patterns, enables incremental delivery, and minimizes risk. Key success factors include stakeholder clarification on workflow rules, proper integration with E5-004 and E5-005, and comprehensive test coverage.

The analysis identifies clear patterns to follow (Forecast, Baseline Log), reusable abstractions, and a phased implementation approach that aligns with TDD discipline and working agreements. Estimated effort is 50-68 hours across 4 phases, with Phase 1 (Basic CRUD) recommended as the starting point.

---

**Analysis Complete - Ready for Stakeholder Review and Detailed Planning**
