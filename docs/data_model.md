# Data Model for Project Budget Management & EVM Analytics System

## Overview

This document defines the data model for the Project Budget Management and Earned Value Management (EVM) system. The model is designed to support the hierarchical project structure (Project → WBE → Cost Element) and all financial tracking, forecasting, and EVM analytics requirements as defined in the PRD.

Based on the example data provided, this model captures project events over time including budget changes, forecasts, actuals, and quality events, enabling comprehensive financial analysis and EVM calculations.

---

## Core Entities

### 1. Project

The top-level container for all project-related information.

**Primary Key:** `project_id`

**Attributes:**
- `project_id` (UUID, PK) - Unique system-generated identifier
- `project_name` (STRING, 200) - Name of the project
- `customer_name` (STRING, 200) - Customer organization name
- `contract_value` (DECIMAL 15,2) - Total contracted project value
- `project_code` (STRING, 100, NULL) - Internal project code/reference (e.g., from quotation)
- `pricelist_code` (STRING, 100, NULL) - Pricelist reference (e.g., "LISTINO 118")
- `start_date` (DATE) - Project start date
- `planned_completion_date` (DATE) - Original planned completion date
- `actual_completion_date` (DATE, NULL) - Actual completion date when finished
- `project_manager_id` (UUID, FK → User) - Assigned project manager
- `status` (ENUM) - Current project status (active, on-hold, completed, cancelled)
- `notes` (TEXT, NULL) - General project notes and context
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Has many **WBEs**
- Has many **Project Events**

---

### 2. Work Breakdown Element (WBE)

Represents an individual machine or major deliverable within a project. Derived from image data showing multiple phases/tracking points.

**Primary Key:** `wbe_id`

**Attributes:**
- `wbe_id` (UUID, PK) - Unique system-generated identifier
- `project_id` (UUID, FK → Project) - Parent project
- `machine_type` (STRING, 100) - Type or category of machine
- `serial_number` (STRING, 100, NULL) - Machine serial number or identifier
- `contracted_delivery_date` (DATE, NULL) - Contractually specified delivery date
- `revenue_allocation` (DECIMAL 15,2) - Revenue assigned to this WBE
- `status` (ENUM) - Current WBE status (designing, in-production, shipped, commissioning, completed)
- `notes` (TEXT, NULL) - WBE-specific notes
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Project**
- Has many **Cost Elements**
- Has many **WBE Events**

---

### 3. Cost Element

Represents a department or discipline responsible for specific work within a WBE. From image: departments like "sales", "syseng", "ut", "sw", "field", "pm", "produzione", "collaudi", "cliente".

**Primary Key:** `cost_element_id`

**Attributes:**
- `cost_element_id` (UUID, PK) - Unique system-generated identifier
- `wbe_id` (UUID, FK → WBE) - Parent WBE
- `cost_element_type_id` (UUID, FK → Cost Element Type) - Type/category of cost element
- `department_code` (STRING, 50) - Department identifier (sales, syseng, ut, sw, field, pm, produzione, collaudi, cliente)
- `department_name` (STRING, 100) - Full department name
- `budget_bac` (DECIMAL 15,2) - Budget at Completion (BAC) for this cost element
- `revenue_plan` (DECIMAL 15,2) - Planned revenue allocation for this cost element
- `status` (ENUM) - Current status (planned, active, completed, cancelled)
- `notes` (TEXT, NULL) - Cost element notes
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **WBE**
- Belongs to **Cost Element Type**
- Has one **Cost Element Schedule** (schedule baseline)
- Has many **Cost Registrations**
- Has many **Forecasts**
- Has many **Quality Events**

---

### 4. User

System users with role-based access.

**Primary Key:** `user_id`

**Attributes:**
- `user_id` (UUID, PK) - Unique system-generated identifier
- `username` (STRING, 100, UNIQUE) - Login username
- `email` (STRING, 200, UNIQUE) - User email address
- `full_name` (STRING, 200) - Full name of user
- `role` (ENUM) - User role (admin, project_manager, department_manager, controller, executive_viewer)
- `department` (STRING, 100, NULL) - Department association if applicable
- `is_active` (BOOLEAN) - Active user flag
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

---

## Event Tables

### 9. Project Event

Tracks all significant events at the project level. From image: phase changes, milestone achievements, official communications.

**Primary Key:** `event_id`

**Attributes:**
- `event_id` (UUID, PK) - Unique system-generated identifier
- `project_id` (UUID, FK → Project) - Associated project
- `event_date` (DATE) - Date when event occurred
- `event_type` (ENUM) - Type: aperture, technical_release, internal_test_start, construction_start, testing, closure, etc.
- `department` (STRING, 100) - Department responsible/associated with event
- `description` (TEXT) - Detailed event description (e.g., "creazione commessa", "ufficializzazione forecast", "chiusura progetto")
- `notes` (TEXT, NULL) - Additional notes or comments
- `created_by` (UUID, FK → User) - User who created the event
- `created_at` (TIMESTAMP) - Record creation timestamp
- `last_modified_at` (TIMESTAMP) - Last modification timestamp
- `is_deleted` (BOOLEAN, DEFAULT FALSE) - Soft delete flag

**Relationships:**
- Belongs to **Project**
- Belongs to **User** (created_by)

---

### 10. Baseline Snapshot

Captures baseline state at specific project milestones. From image: specific date points where baseline values are recorded.

**Primary Key:** `baseline_id`

**Attributes:**
- `baseline_id` (UUID, PK) - Unique system-generated identifier
- `project_id` (UUID, FK → Project) - Associated project
- `baseline_date` (DATE) - Date of baseline creation
- `milestone_type` (ENUM) - Milestone: kickoff, bom_release, engineering_complete, procurement_complete, manufacturing_start, shipment, site_arrival, commissioning_start, commissioning_complete, closeout
- `description` (TEXT, NULL) - Milestone description
- `department` (STRING, 100, NULL) - Responsible department
- `is_pmb` (BOOLEAN) - True if this is the Performance Measurement Baseline
- `created_by` (UUID, FK → User) - User who created baseline
- `created_at` (TIMESTAMP) - Record creation timestamp

**Relationships:**
- Belongs to **Project**
- Has many **Baseline Cost Elements**

---

### 11. Baseline Cost Element

Captures cost element state at baseline creation.

**Primary Key:** `baseline_cost_element_id`

**Attributes:**
- `baseline_cost_element_id` (UUID, PK) - Unique system-generated identifier
- `baseline_id` (UUID, FK → Baseline Snapshot) - Parent baseline
- `cost_element_id` (UUID, FK → Cost Element) - Referenced cost element
- `budget_bac` (DECIMAL 15,2) - Snapshot of BAC
- `revenue` (DECIMAL 15,2) - Snapshot of revenue
- `forecast_eac` (DECIMAL 15,2, NULL) - Snapshot of EAC forecast
- `actual_ac` (DECIMAL 15,2, NULL) - Snapshot of actual cost
- `earned_ev` (DECIMAL 15,2, NULL) - Snapshot of earned value

---

## Financial Tracking Tables

### 12. Budget Allocation

Tracks budget allocations and changes over time. From image: p0, revenues columns showing values at different points.

**Primary Key:** `budget_allocation_id`

**Attributes:**
- `budget_allocation_id` (UUID, PK) - Unique system-generated identifier
- `cost_element_id` (UUID, FK → Cost Element) - Target cost element
- `allocation_date` (DATE) - Date of allocation
- `budget_amount` (DECIMAL 15,2) - Allocated budget amount
- `revenue_amount` (DECIMAL 15,2, NULL) - Revenue associated with allocation
- `allocation_type` (ENUM) - Type: initial, change_order, adjustment
- `description` (TEXT, NULL) - Allocation description
- `related_change_order_id` (UUID, FK → Change Order, NULL) - If due to change order
- `created_by` (UUID, FK → User) - User who created allocation
- `created_at` (TIMESTAMP) - Record creation timestamp

**Relationships:**
- Belongs to **Cost Element**
- Belongs to **Change Order** (optional)

---

### 13. Cost Registration

Records actual costs incurred. From image: "actual" column tracking real expenditures over time.

**Primary Key:** `cost_registration_id`

**Attributes:**
- `cost_registration_id` (UUID, PK) - Unique system-generated identifier
- `cost_element_id` (UUID, FK → Cost Element) - Target cost element
- `registration_date` (DATE) - Date cost was incurred
- `amount` (DECIMAL 15,2) - Cost amount
- `cost_category` (ENUM) - Category: labor, materials, subcontracts, other
- `invoice_number` (STRING, 100, NULL) - Reference invoice or PO number
- `description` (TEXT) - Cost description and details
- `is_quality_cost` (BOOLEAN, DEFAULT FALSE) - True if this is a quality event cost
- `quality_event_id` (UUID, FK → Quality Event, NULL) - If part of quality event
- `created_by` (UUID, FK → User) - User who registered cost
- `created_at` (TIMESTAMP) - Record creation timestamp
- `last_modified_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Cost Element**
- Belongs to **Quality Event** (optional)

---

### 14. Baseline Log

Maintains a log of all baseline creation events. Each baseline is identified by a unique baseline_id and can be associated with schedule baselines, earned value baselines, or other baseline types.

**Primary Key:** `baseline_id`

**Attributes:**
- `baseline_id` (UUID, PK) - Unique system-generated identifier
- `baseline_type` (ENUM) - Type: schedule, earned_value, budget, forecast, combined
- `baseline_date` (DATE) - Date when baseline was created
- `description` (TEXT, NULL) - Description of the baseline
- `created_by` (UUID, FK → User) - User who created baseline
- `created_at` (TIMESTAMP) - Record creation timestamp

**Relationships:**
- Has many **Cost Element Schedules** (schedule baselines)
- Has many **Earned Value Entries** (earned value baselines)
- Belongs to **User** (created_by)

---

### 15. Cost Element Schedule

Defines the schedule baseline for a cost element, used to calculate Planned Value (PV). The schedule includes start date, end date, and progression type that determines how planned completion percentage is calculated over time.

**Primary Key:** `schedule_id`

**Attributes:**
- `schedule_id` (UUID, PK) - Unique system-generated identifier
- `cost_element_id` (UUID, FK → Cost Element, UNIQUE) - Target cost element (one schedule per cost element)
- `baseline_id` (UUID, FK → Baseline Log, NULL) - Reference to baseline log entry when schedule is baselined
- `start_date` (DATE) - Planned start date for the cost element
- `end_date` (DATE) - Planned end date for the cost element
- `progression_type` (ENUM) - Type: linear, gaussian, logarithmic
- `notes` (TEXT, NULL) - Schedule notes and assumptions
- `created_by` (UUID, FK → User) - User who created schedule
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Cost Element**
- Belongs to **Baseline Log** (optional, when baselined)

**Notes:**
- Planned Value (PV) is calculated as: $PV = BAC \times \%\ \text{di completamento pianificato}$
- The planned completion percentage is derived from the schedule baseline using the progression type:
  - Linear: Even distribution over duration
  - Gaussian: Normal distribution curve with peak at midpoint
  - Logarithmic: Slow start with accelerating completion
- When a schedule is baselined, it references a Baseline Log entry via baseline_id

---

### 16. Earned Value Entry

Records the percentage of work completed (physical progress) for a cost element, used to calculate Earned Value (EV). The earned value percentage must be baselined and maintained as historical record.

**Primary Key:** `earned_value_id`

**Attributes:**
- `earned_value_id` (UUID, PK) - Unique system-generated identifier
- `cost_element_id` (UUID, FK → Cost Element) - Target cost element
- `baseline_id` (UUID, FK → Baseline Log, NULL) - Reference to baseline log entry when earned value is baselined
- `completion_date` (DATE) - Date when work completion was measured
- `percent_complete` (DECIMAL 5,2) - Percentage of physical work completed (0-100)
- `earned_value` (DECIMAL 15,2, NULL) - Calculated Earned Value (EV = BAC × percent_complete)
- `deliverables` (TEXT, NULL) - Description of deliverables achieved
- `description` (TEXT, NULL) - Additional context
- `created_by` (UUID, FK → User) - User who recorded earned value
- `created_at` (TIMESTAMP) - Record creation timestamp
- `last_modified_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Cost Element**
- Belongs to **Baseline Log** (optional, when baselined)

**Notes:**
- Earned Value (EV) is calculated as: $EV = BAC \times \%\ \text{di completamento fisico}$
- Example: if $BAC = €100{,}000$ and percent_complete = 30%, then $EV = €30{,}000$
- When earned value entries are baselined, they reference a Baseline Log entry via baseline_id for historical comparison and trend analysis

---

### 17. Forecast

Tracks cost and revenue forecasts over time. From image: "forecast" column showing EAC projections at different dates.

**Primary Key:** `forecast_id`

**Attributes:**
- `forecast_id` (UUID, PK) - Unique system-generated identifier
- `cost_element_id` (UUID, FK → Cost Element) - Target cost element
- `forecast_date` (DATE) - Date when forecast was created
- `estimate_at_completion` (DECIMAL 15,2) - Estimate at Completion (EAC)

- `assumptions` (TEXT, NULL) - Assumptions underlying the forecast
- `estimator_id` (UUID, FK → User) - User who created forecast
- `forecast_type` (ENUM) - Type: bottom_up, performance_based, management_judgment
- `created_at` (TIMESTAMP) - Record creation timestamp
- `last_modified_at` (TIMESTAMP) - Last modification timestamp
- `is_current` (BOOLEAN, DEFAULT FALSE) - True for the current forecast version

**Relationships:**
- Belongs to **Cost Element**

---

## Change Order and Quality Management

### 18. Change Order

Manages scope changes and contract modifications. From image: "change order" references in notes.

**Primary Key:** `change_order_id`

**Attributes:**
- `change_order_id` (UUID, PK) - Unique system-generated identifier
- `project_id` (UUID, FK → Project) - Associated project
- `wbe_id` (UUID, FK → WBE, NULL) - Specific WBE if applicable, NULL if project-wide
- `change_order_number` (STRING, 50, UNIQUE) - Unique change order identifier
- `title` (STRING, 200) - Change order title
- `description` (TEXT) - Detailed description of the change
- `requesting_party` (STRING, 100) - Customer, internal, subcontractor, etc.
- `justification` (TEXT, NULL) - Business case for the change
- `effective_date` (DATE) - Proposed/actual effective date
- `cost_impact` (DECIMAL 15,2, NULL) - Total cost impact
- `revenue_impact` (DECIMAL 15,2, NULL) - Total revenue impact
- `status` (ENUM) - Status: draft, submitted, under_review, approved, rejected, implemented
- `created_by` (UUID, FK → User) - Creator
- `created_at` (TIMESTAMP) - Record creation timestamp
- `approved_by` (UUID, FK → User, NULL) - Approver
- `approved_at` (TIMESTAMP, NULL) - Approval timestamp
- `implemented_by` (UUID, FK → User, NULL) - Implementer
- `implemented_at` (TIMESTAMP, NULL) - Implementation timestamp

**Relationships:**
- Belongs to **Project**
- Belongs to **WBE** (optional)

---

### 19. Change Order Line Item

Details specific budget/revenue changes within a change order.

**Primary Key:** `change_order_line_id`

**Attributes:**
- `change_order_line_id` (UUID, PK) - Unique system-generated identifier
- `change_order_id` (UUID, FK → Change Order) - Parent change order
- `cost_element_id` (UUID, FK → Cost Element) - Target cost element
- `budget_change` (DECIMAL 15,2) - Change to budget (can be negative)
- `revenue_change` (DECIMAL 15,2) - Change to revenue (can be negative)
- `description` (TEXT, NULL) - Line item description

**Relationships:**
- Belongs to **Change Order**
- Belongs to **Cost Element**

---

### 20. Quality Event

Tracks quality issues and non-conformities. From image: root causes like "non conformità", "garanzia", "forecasting" issues.

**Primary Key:** `quality_event_id`

**Attributes:**
- `quality_event_id` (UUID, PK) - Unique system-generated identifier
- `project_id` (UUID, FK → Project) - Associated project
- `wbe_id` (UUID, FK → WBE, NULL) - Specific WBE if applicable
- `cost_element_id` (UUID, FK → Cost Element, NULL) - Specific cost element if applicable
- `event_date` (DATE) - Date when quality issue occurred or was discovered
- `title` (STRING, 200) - Summary title
- `description` (TEXT) - Detailed description of the quality issue
- `root_cause` (ENUM) - Classification: non_conformita, forecasting, ordine_integrativo, baseline, scrittura_actual, garanzia, closure, etc.
- `responsible_department` (STRING, 100) - Department responsible for the issue
- `estimated_cost_impact` (DECIMAL 15,2, NULL) - Initially estimated cost impact
- `actual_cost_impact` (DECIMAL 15,2, NULL) - Actual cost incurred
- `corrective_actions` (TEXT, NULL) - Actions taken to address issue
- `preventive_measures` (TEXT, NULL) - Measures to prevent recurrence
- `status` (ENUM) - Status: identified, investigating, corrective_action_planned, corrective_action_in_progress, resolved
- `created_by` (UUID, FK → User) - Creator
- `created_at` (TIMESTAMP) - Record creation timestamp
- `resolved_date` (DATE, NULL) - Date when issue was resolved

**Relationships:**
- Belongs to **Project**
- Belongs to **WBE** (optional)
- Belongs to **Cost Element** (optional)

---

## Calculated/Aggregated Views

### 21. EVM Metrics (Calculated View)

Provides real-time EVM calculations aggregated at multiple levels.

**Source:** Calculated from Budget Allocations, Baseline Log, Cost Element Schedules, Cost Registrations, Earned Value Entries, and Forecasts

**Calculation Notes:**
- **Planned Value (PV)**: Calculated from Cost Element Schedule (referenced via Baseline Log) using $PV = BAC \times \%\ \text{di completamento pianificato}$, where planned completion percentage is derived from the schedule baseline (start date, end date, progression type) at the control date
- **Earned Value (EV)**: Calculated from Earned Value Entry (referenced via Baseline Log) using $EV = BAC \times \%\ \text{di completamento fisico}$, where physical completion percentage is from recorded earned value entries

**Attributes:**
- `record_id` (UUID, PK) - Unique identifier
- `entity_type` (ENUM) - Level: project, wbe, cost_element
- `entity_id` (UUID) - ID of project, WBE, or cost element
- `as_of_date` (DATE) - Point in time for calculation
- `planned_value_pv` (DECIMAL 15,2) - Planned Value
- `earned_value_ev` (DECIMAL 15,2) - Earned Value
- `actual_cost_ac` (DECIMAL 15,2) - Actual Cost
- `budget_at_completion_bac` (DECIMAL 15,2) - Budget at Completion
- `estimate_at_completion_eac` (DECIMAL 15,2) - Estimate at Completion
- `estimate_to_complete_etc` (DECIMAL 15,2) - Estimate to Complete
- `cost_variance_cv` (DECIMAL 15,2) - Cost Variance (EV - AC)
- `schedule_variance_sv` (DECIMAL 15,2) - Schedule Variance (EV - PV)
- `variance_at_completion_vac` (DECIMAL 15,2) - Variance at Completion (BAC - EAC)
- `cost_performance_index_cpi` (DECIMAL 5,4) - CPI (EV / AC)
- `schedule_performance_index_spi` (DECIMAL 5,4) - SPI (EV / PV)
- `to_complete_performance_index_tcpi_bac` (DECIMAL 5,4, NULL) - TCPI based on BAC
- `to_complete_performance_index_tcpi_eac` (DECIMAL 5,4, NULL) - TCPI based on EAC
- `percent_complete_budget` (DECIMAL 5,2) - AC / BAC
- `percent_complete_earned` (DECIMAL 5,2) - EV / BAC
- `percent_complete_schedule` (DECIMAL 5,2) - (current_date - start) / duration
- `revenue` (DECIMAL 15,2) - Total revenue
- `margine_su_venduto` (DECIMAL 5,2, NULL) - Margin on sold items (percent)
- `margine_forecast` (DECIMAL 5,2, NULL) - Forecast margin (percent)
- `completion_percent` (DECIMAL 5,2) - Overall completion percentage

---

## Audit and History

### 22. Audit Log

Maintains complete audit trail of all data changes.

**Primary Key:** `audit_log_id`

**Attributes:**
- `audit_log_id` (UUID, PK) - Unique system-generated identifier
- `entity_type` (STRING, 50) - Type of entity modified
- `entity_id` (UUID) - ID of modified entity
- `action` (ENUM) - Action: create, update, delete, approve, reject, implement
- `field_name` (STRING, 100, NULL) - Specific field if applicable
- `old_value` (TEXT, NULL) - Previous value
- `new_value` (TEXT, NULL) - New value
- `reason` (TEXT, NULL) - Reason for change if provided
- `user_id` (UUID, FK → User) - User who made the change
- `timestamp` (TIMESTAMP) - When change occurred
- `ip_address` (STRING, 45, NULL) - IP address of user
- `user_agent` (STRING, 500, NULL) - User agent string

**Relationships:**
- Belongs to **User**

---

## Additional Reference Tables

### 23. Department

Lookup table for departments.

**Primary Key:** `department_id`

**Attributes:**
- `department_id` (UUID, PK) - Unique identifier
- `department_code` (STRING, 20, UNIQUE) - Department code (sales, syseng, ut, sw, etc.)
- `department_name` (STRING, 100) - Full department name
- `description` (TEXT, NULL) - Department description
- `is_active` (BOOLEAN) - Active flag

---

### 24. Project Phase

Lookup table for project phases/milestones.

**Primary Key:** `phase_id`

**Attributes:**
- `phase_id` (UUID, PK) - Unique identifier
- `phase_code` (STRING, 50, UNIQUE) - Phase code
- `phase_name` (STRING, 100) - Full phase name
- `description` (TEXT, NULL) - Phase description
- `display_order` (INTEGER) - Order for display

**Example values:**
- aperture (Opening/Kickoff)
- rilascio_tecnico (Technical Release)
- inizio_collaudi_interni (Start Internal Testing)
- inizio_cantiere (Start Construction Site)
- collaudo (Testing/Acceptance)
- chiusura (Closure)

---

### 25. Cost Element Type

Lookup table for cost element types, used to categorize Cost Elements by labor/department category.

**Primary Key:** `cost_element_type_id`

**Attributes:**
- `cost_element_type_id` (UUID, PK) - Unique identifier
- `type_code` (STRING, 50, UNIQUE) - Cost element type code (labor category code)
- `type_name` (STRING, 200) - Full type name
- `category_type` (ENUM) - Type: engineering_mechanical, engineering_electrical, software, assembly, commissioning, management, support, material, other
- `tracks_hours` (BOOLEAN) - True if category tracks both hours and cost
- `description` (TEXT, NULL) - Type description
- `display_order` (INTEGER) - Order for display
- `is_active` (BOOLEAN) - Active flag
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Referenced by **Cost Element**

**Example values** (partial list):
- `utm_robot` / `utm_robot_h` - Robot Mechanical Engineering
- `utm_lgv` / `utm_lgv_h` - LGV Mechanical Engineering
- `ute` / `ute_h` - Electrical Engineering
- `sw_pc` / `sw_pc_h` - PC Software Development
- `sw_plc` / `sw_plc_h` - PLC Software Development
- `mtg_mec` / `mtg_mec_h` - Mechanical Assembly
- `cab_ele` / `cab_ele_h` - Electrical Cabinet Assembly
- `coll_ba` / `coll_ba_h` - Busbar Commissioning
- `coll_pc` / `coll_pc_h` - PC Commissioning
- `coll_plc` / `coll_plc_h` - PLC Commissioning
- `pm_cost` / `pm_h` - Project Management
- `document` / `document_h` - Documentation
- `site` / `site_h` - Site Engineering
- `install` / `install_h` - Installation
- `av_pc` / `av_pc_h` - PC Warranty/Support
- `mat` - Materials
- `spese_pm` - Project Management Expenses
- `spese_field` - Field Expenses
- `imballo` - Packaging
- `stoccaggio` - Storage
- `trasporto` - Transportation

---

## Entity Relationship Summary

```
Project
  ├── Has Many: WBE
  │      ├── Has Many: Cost Element
  │      │      ├── Has One: Cost Element Schedule
  │      │      ├── Has Many: Cost Registration
  │      │      ├── Has Many: Earned Value Entry
  │      │      ├── Has Many: Forecast
  │      │      ├── Has Many: Budget Allocation
  │      │      └── Has Many: Quality Event
  │      └── Has Many: Change Order Line Item
  ├── Has Many: Project Event
  ├── Has Many: Baseline Snapshot
  │      └── Has Many: Baseline Cost Element
  ├── Has Many: Change Order
  │      └── Has Many: Change Order Line Item
  └── Has Many: Quality Event

Baseline Log
  ├── Has Many: Cost Element Schedules (schedule baselines)
  └── Has Many: Earned Value Entries (earned value baselines)

User
  ├── Has Many: Audit Log
  └── Created/Modified all event records

Department (Reference)
Project Phase (Reference)
Cost Element Type (Reference)
  └── Referenced by Cost Element
```

---

## Key Design Decisions

1. **Hierarchical Structure**: Three-level hierarchy (Project → WBE → Cost Element) supports granular tracking while enabling roll-ups.

2. **Event-Based Model**: All financial changes tracked through events, preserving history and auditability.

3. **EVM Calculations**: Computed from source data. Optional `EVM_Metrics` view can be materialized for performance.

4. **Soft Deletes**: Events use `is_deleted` to keep data integrity while supporting corrections.

5. **Change Order Impact**: Separate line items show per-cost-element changes for detailed analysis.

6. **Quality Cost Tracking**: `is_quality_cost` and links to `quality_event_id` separate quality from planned costs.

7. **Forecast Versioning**: `is_current` marks the active forecast per cost element.

8. **Baseline Snapshotting**: Separate table stores baseline state to compare against current actuals.

9. **Audit Trail**: `Audit_Log` tracks all modifications with before/after values.

10. **Multi-Level Aggregation**: EVM metrics calculable at project, WBE, and cost element levels.

11. **Cost Element Type Classification**: Cost Elements are classified by type through the `Cost Element Type` lookup table, which incorporates labor/department category codes (e.g., utm_robot, sw_pc, mtg_mec). This enables standardized categorization and analysis of cost elements across all projects with built-in labor category definitions.

12. **Schedule Baseline for Planned Value**: Each Cost Element has a schedule baseline (Cost Element Schedule) with start date, end date, and progression type (linear, gaussian, logarithmic). Planned Value (PV) is calculated as $PV = BAC \times \%\ \text{di completamento pianificato}$, where the planned completion percentage is derived from the schedule baseline at any control date.

13. **Baseline Log**: All baselines are tracked in a Baseline Log table with a unique baseline_id. Schedule baselines and earned value baselines reference this log via baseline_id, ensuring proper baseline identification and historical tracking.

14. **Earned Value Baseline**: Earned Value (EV) is calculated from baselined percentage of work completed using $EV = BAC \times \%\ \text{di completamento fisico}$. The earned value entries track physical completion percentages which reference Baseline Log entries via baseline_id for historical comparison and trend analysis.

---

## Data Validation Rules

Based on PRD Section 15.1:

1. Sum of WBE revenues ≤ Project contract value
2. Sum of WBE budgets ≤ Project total budget
3. Sum of Cost Element budgets within a WBE ≤ WBE allocation
4. Cost Registrations only after Cost Element start date
5. Earned Value ≤ Planned Value (unless authorized override)
6. Forecast EAC ≥ 0
7. Actual Cost ≥ 0
8. Budget amounts ≥ 0
9. Revenue allocations ≥ 0
10. Percent complete values between 0-100

---

## Example Data Mapping from Image

Mapping columns from the example image to the data model:

| Image Column | Data Model Mapping |
|-------------|-------------------|
| fase (Phase) | Project Event.event_type / Project Phase |
| data (Date) | Project Event.event_date, other event dates |
| reparto (Department) | Cost Element.department_code |
| note (Notes) | Project Event.description, various notes fields |
| p0 | Baseline Snapshot budget value |
| revenues | Budget Allocation.revenue_amount, aggregated |
| forecast | Forecast.estimate_at_completion |
| actual | Cost Registration.amount, aggregated to AC |
| PV (planned value) | Cost Element Schedule, calculated as BAC × planned completion % |
| EV (earned value) | Earned Value Entry, calculated as BAC × physical completion % |
| root cause | Quality Event.root_cause |
| delta costi | Change Order Line Item.budget_change |
| delta forecast | Calculated from Forecast history |
| delta revenues | Change Order Line Item.revenue_change |
| margine su venduto | Calculated: ((Revenue - Cost) / Revenue) * 100 |
| margine forecast | Calculated: ((Revenue - EAC) / Revenue) * 100 |
| completion | Calculated: (EV / BAC) * 100 |
| ETC | Forecast.estimate_to_complete |

---

## Next Steps

1. Physical schema design for the target database (PostgreSQL recommended)
2. Index strategy for performance
3. Calculation engine for EVM metrics
4. API design for data access and manipulation
5. Dashboard and reporting queries
6. Data migration procedures

