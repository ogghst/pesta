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
- Has many **Product Groups**
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

### 5. Product Group

Represents a logical grouping of products/machines in a quotation (from quotation structure). Maps to the `product_groups` array in the quotation JSON.

**Primary Key:** `product_group_id`

**Attributes:**
- `product_group_id` (UUID, PK) - Unique system-generated identifier
- `project_id` (UUID, FK → Project) - Parent project
- `group_code` (STRING, 50) - Group identifier (e.g., "TXT", "TXT-22")
- `group_name` (STRING, 200) - Full name of the product group
- `quantity` (INTEGER) - Number of units in this group
- `pricelist_subtotal` (DECIMAL 15,2, NULL) - Subtotal from pricelist
- `cost_subtotal` (DECIMAL 15,2, NULL) - Total cost for this group
- `offer_price` (DECIMAL 15,2, NULL) - Offered price
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Project**
- Has many **Quotation Categories**

---

### 6. Quotation Category

Represents a category within a product group (maps to `categories` array in quotation JSON).

**Primary Key:** `quotation_category_id`

**Attributes:**
- `quotation_category_id` (UUID, PK) - Unique system-generated identifier
- `product_group_id` (UUID, FK → Product Group) - Parent product group
- `category_code` (STRING, 50) - Category identifier (e.g., "J0ZZ", "PCZZ")
- `category_name` (STRING, 200) - Full category name
- `wbe_id` (UUID, FK → WBE, NULL) - Optional link to WBE if mapping exists
- `pricelist_subtotal` (DECIMAL 15,2, NULL) - Subtotal from pricelist
- `cost_subtotal` (DECIMAL 15,2, NULL) - Total cost
- `offer_price` (DECIMAL 15,2, NULL) - Offered price
- `margin_amount` (DECIMAL 15,2, NULL) - Margin in absolute value
- `margin_percentage` (DECIMAL 5,2, NULL) - Margin as percentage
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Product Group**
- Belongs to **WBE** (optional)
- Has many **Quotation Items**

---

### 7. Quotation Item

Represents an individual item within a quotation category (maps to `items` array in quotation JSON).

**Primary Key:** `quotation_item_id`

**Attributes:**
- `quotation_item_id` (UUID, PK) - Unique system-generated identifier
- `quotation_category_id` (UUID, FK → Quotation Category) - Parent category
- `position` (STRING, 20, NULL) - Item position number
- `code` (STRING, 100) - Item code (e.g., "J0ZZ-PM", "PM")
- `cod_listino` (STRING, 100, NULL) - Pricelist code
- `description` (STRING, 500) - Item description
- `internal_code` (STRING, 100, NULL) - Internal reference code
- `quantity` (DECIMAL 10,2) - Quantity ordered
- `pricelist_unit_price` (DECIMAL 15,2, NULL) - Unit price from pricelist
- `pricelist_total_price` (DECIMAL 15,2, NULL) - Total price from pricelist
- `unit_cost` (DECIMAL 15,2, NULL) - Unit cost
- `total_cost` (DECIMAL 15,2, NULL) - Total cost
- `priority_order` (INTEGER, NULL) - Priority ranking
- `priority` (INTEGER, NULL) - Priority level
- `line_number` (INTEGER, NULL) - Line number in quotation
- `wbs` (STRING, 100, NULL) - Work Breakdown Structure code
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Quotation Category**
- Has many **Quotation Item Labor Costs**

---

### 8. Quotation Item Labor Cost

Tracks detailed labor cost breakdown for each quotation item by department/labor type. Maps to the detailed cost fields in the quotation JSON (utm_robot, sw_pc, mtg_mec, etc.).

**Primary Key:** `quotation_item_labor_cost_id`

**Attributes:**
- `quotation_item_labor_cost_id` (UUID, PK) - Unique system-generated identifier
- `quotation_item_id` (UUID, FK → Quotation Item) - Parent quotation item
- `labor_category_code` (STRING, 50) - Labor category code (see Department Labor Category mapping)
- `hours` (DECIMAL 10,2, NULL) - Hours allocated
- `cost` (DECIMAL 15,2, NULL) - Cost allocated
- `created_at` (TIMESTAMP) - Record creation timestamp
- `updated_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Quotation Item**
- Links to labor category codes (see Department Labor Category)

**Note:** Labor category codes from quotation structure:
- `utm_robot`, `utm_robot_h` - Robot mechanical engineering
- `utm_lgv`, `utm_lgv_h` - LGV mechanical engineering
- `utm_intra`, `utm_intra_h` - Internal mechanical engineering
- `utm_layout`, `utm_layout_h` - Layout mechanical engineering
- `ute`, `ute_h` - Electrical engineering
- `ba`, `ba_h` - Busbar assembly
- `sw_pc`, `sw_pc_h` - PC software
- `sw_plc`, `sw_plc_h` - PLC software
- `sw_lgv`, `sw_lgv_h` - LGV software
- `mtg_mec`, `mtg_mec_h` - Mechanical assembly
- `mtg_mec_intra`, `mtg_mec_intra_h` - Internal mechanical assembly
- `cab_ele`, `cab_ele_h` - Electrical cabinet assembly
- `cab_ele_intra`, `cab_ele_intra_h` - Internal electrical cabinet assembly
- `coll_ba`, `coll_ba_h` - Busbar commissioning
- `coll_pc`, `coll_pc_h` - PC commissioning
- `coll_plc`, `coll_plc_h` - PLC commissioning
- `coll_lgv`, `coll_lgv_h` - LGV commissioning
- `pm_cost`, `pm_h` - Project management
- `document`, `document_h` - Documentation
- `site`, `site_h` - Site engineering
- `install`, `install_h` - Installation
- `av_pc`, `av_pc_h` - PC warranty/support
- `av_plc`, `av_plc_h` - PLC warranty/support
- `av_lgv`, `av_lgv_h` - LGV warranty/support
- `spese_pm` - Project management expenses
- `spese_field` - Field expenses
- `spese_varie` - Various expenses
- `imballo` - Packaging
- `stoccaggio` - Storage
- `trasporto` - Transportation
- `after_sales` - After sales service
- `provvigioni_italia` - Italian commissions
- `provvigioni_estero` - Foreign commissions
- `tesoretto` - Treasury/cash flow
- `montaggio_bema_mbe_us` - Special assembly
- `mat` - Materials
- `total` - Total

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

### 14. Earned Value Entry

Records earned value based on work completion. From image: work progress reflected in completion percentages.

**Primary Key:** `earned_value_id`

**Attributes:**
- `earned_value_id` (UUID, PK) - Unique system-generated identifier
- `cost_element_id` (UUID, FK → Cost Element) - Target cost element
- `completion_date` (DATE) - Date when work was completed/measured
- `earned_value` (DECIMAL 15,2) - Earned Value (EV) amount
- `percent_complete` (DECIMAL 5,2, NULL) - Percentage of work completed
- `deliverables` (TEXT, NULL) - Description of deliverables achieved
- `description` (TEXT, NULL) - Additional context
- `created_by` (UUID, FK → User) - User who recorded earned value
- `created_at` (TIMESTAMP) - Record creation timestamp
- `last_modified_at` (TIMESTAMP) - Last modification timestamp

**Relationships:**
- Belongs to **Cost Element**

---

### 15. Forecast

Tracks cost and revenue forecasts over time. From image: "forecast" column showing EAC projections at different dates.

**Primary Key:** `forecast_id`

**Attributes:**
- `forecast_id` (UUID, PK) - Unique system-generated identifier
- `cost_element_id` (UUID, FK → Cost Element) - Target cost element
- `forecast_date` (DATE) - Date when forecast was created
- `estimate_at_completion` (DECIMAL 15,2) - Estimate at Completion (EAC)
- `estimate_to_complete` (DECIMAL 15,2, NULL) - Estimate to Complete (ETC)
- `forecast_revenue` (DECIMAL 15,2, NULL) - Forecasted revenue
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

### 16. Change Order

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

### 17. Change Order Line Item

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

### 18. Quality Event

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

### 19. EVM Metrics (Calculated View)

Provides real-time EVM calculations aggregated at multiple levels.

**Source:** Calculated from Budget Allocations, Cost Registrations, Earned Value Entries, and Forecasts

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

### 20. Audit Log

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

### 21. Department

Lookup table for departments.

**Primary Key:** `department_id`

**Attributes:**
- `department_id` (UUID, PK) - Unique identifier
- `department_code` (STRING, 20, UNIQUE) - Department code (sales, syseng, ut, sw, etc.)
- `department_name` (STRING, 100) - Full department name
- `description` (TEXT, NULL) - Department description
- `is_active` (BOOLEAN) - Active flag

---

### 22. Project Phase

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

### 23. Labor Category

Lookup table for labor/department categories referenced in quotations.

**Primary Key:** `labor_category_id`

**Attributes:**
- `labor_category_id` (UUID, PK) - Unique identifier
- `category_code` (STRING, 50, UNIQUE) - Labor category code (matches quotation codes)
- `category_name` (STRING, 200) - Full category name
- `category_type` (ENUM) - Type: engineering_mechanical, engineering_electrical, software, assembly, commissioning, management, support, material, other
- `tracks_hours` (BOOLEAN) - True if category tracks both hours and cost
- `description` (TEXT, NULL) - Category description
- `display_order` (INTEGER) - Order for display
- `is_active` (BOOLEAN) - Active flag

**Relationships:**
- Referenced by **Quotation Item Labor Cost**

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
  │      │      ├── Has Many: Cost Registration
  │      │      ├── Has Many: Earned Value Entry
  │      │      ├── Has Many: Forecast
  │      │      ├── Has Many: Budget Allocation
  │      │      └── Has Many: Quality Event
  │      └── Has Many: Change Order Line Item
  ├── Has Many: Product Group
  │      ├── Has Many: Quotation Category
  │      │      ├── Has Many: Quotation Item
  │      │      │      └── Has Many: Quotation Item Labor Cost
  │      │      └── Links to WBE (optional)
  │      └── Has Many: Quotation Category
  ├── Has Many: Project Event
  ├── Has Many: Baseline Snapshot
  │      └── Has Many: Baseline Cost Element
  ├── Has Many: Change Order
  │      └── Has Many: Change Order Line Item
  └── Has Many: Quality Event

User
  ├── Has Many: Audit Log
  └── Created/Modified all event records

Department (Reference)
Project Phase (Reference)
Labor Category (Reference)
  └── Referenced by Quotation Item Labor Cost
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

11. **Quotation Integration**: The quotation structure (Product Group → Category → Item → Labor Cost) provides the initial budget baseline and can optionally map to WBEs and Cost Elements for ongoing tracking. This dual hierarchy supports both quotation-based costing and project execution budgeting.

12. **Labor Cost Granularity**: `Quotation Item Labor Cost` captures department-level cost breakdowns (30+ categories) enabling detailed budget tracking and variance analysis by discipline.

13. **Flexible Mapping**: Optional linking between quotation structure and WBE/Cost Element structures allows for different organizational needs while maintaining traceability.

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

## Quotation to Budget Mapping

The system supports importing quotation data and mapping it to the project budget structure. The mapping enables:

1. **Initial Budget Creation**: Quotation costs can serve as the initial BAC for WBEs and Cost Elements
2. **Cost Tracking**: Labor costs from quotations can be mapped to department Cost Elements
3. **Revenue Recognition**: Pricelist prices from quotations provide revenue allocations
4. **Forecasting**: Use quotation estimates as baseline for forecast comparisons

### Mapping Strategy

**Product Group → WBE Mapping:**
- Product Groups can optionally link to WBEs when a machine/deliverable is clearly identified
- `Quotation Category.wbe_id` provides the linking mechanism
- If no mapping exists, Product Groups remain at the quotation level for reference

**Labor Categories → Cost Elements Mapping:**
- Labor categories from quotations (utm_robot, sw_pc, mtg_mec, etc.) map to department Cost Elements
- The `Labor Category` lookup table provides the mapping between quotation codes and departments
- Multiple quotation items can aggregate costs to a single Cost Element

**Revenue Allocation:**
- `pricelist_total_price` from Quotation Categories provides revenue allocation
- `offer_price` represents negotiated/revisioned revenue
- Revenue is allocated down from Product Group → Category → Item level

**Cost Allocation:**
- `total_cost` from Quotation Items represents planned costs
- Labor costs are tracked at the `Quotation Item Labor Cost` level
- Costs aggregate up through the hierarchy for BAC calculations

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
| root cause | Quality Event.root_cause |
| delta costi | Change Order Line Item.budget_change |
| delta forecast | Calculated from Forecast history |
| delta revenues | Change Order Line Item.revenue_change |
| margine su venduto | Calculated: ((Revenue - Cost) / Revenue) * 100 |
| margine forecast | Calculated: ((Revenue - EAC) / Revenue) * 100 |
| completion | Calculated: (EV / BAC) * 100 |
| ETC | Forecast.estimate_to_complete |

---

## Example Data Mapping from Quotation

Mapping fields from the quotation JSON structure to the data model:

| Quotation JSON Field | Data Model Mapping |
|---------------------|-------------------|
| project.id | Project.project_code |
| project.customer | Project.customer_name |
| project.listino | Project.pricelist_code |
| product_groups[].group_id | Product Group.group_code |
| product_groups[].group_name | Product Group.group_name |
| product_groups[].quantity | Product Group.quantity |
| categories[].category_id | Quotation Category.category_code |
| categories[].wbe | Quotation Category.wbe_id (optional link) |
| categories[].pricelist_subtotal | Quotation Category.pricelist_subtotal |
| categories[].cost_subtotal | Quotation Category.cost_subtotal |
| items[].code | Quotation Item.code |
| items[].description | Quotation Item.description |
| items[].quantity | Quotation Item.quantity |
| items[].unit_cost | Quotation Item.unit_cost |
| items[].total_cost | Quotation Item.total_cost |
| items[].wbs | Quotation Item.wbs |
| items[].utm_robot_h, utm_robot | Quotation Item Labor Cost (labor_category_code: "utm_robot") |
| items[].sw_pc_h, sw_pc | Quotation Item Labor Cost (labor_category_code: "sw_pc") |
| items[].mtg_mec_h, mtg_mec | Quotation Item Labor Cost (labor_category_code: "mtg_mec") |
| items[].pm_cost, pm_h | Quotation Item Labor Cost (labor_category_code: "pm_cost") |
| items[].mat | Quotation Item Labor Cost (labor_category_code: "mat") |
| items[].spese_pm | Quotation Item Labor Cost (labor_category_code: "spese_pm") |
| (all other labor cost fields) | Quotation Item Labor Cost with respective labor_category_code |

---

## Next Steps

1. Physical schema design for the target database (PostgreSQL recommended)
2. Index strategy for performance
3. Calculation engine for EVM metrics
4. API design for data access and manipulation
5. Dashboard and reporting queries
6. Data migration procedures

