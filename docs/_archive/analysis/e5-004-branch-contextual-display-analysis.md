# High-Level Analysis: E5-004 Branch Contextual Display Enhancement

**Task:** E5-004 (Branch Contextual Display - Show Full Project Context in Branch Views)
**Status:** Analysis Phase
**Date:** 2025-11-27
**Last Updated:** 2025-11-27 06:33 CET (Europe/Rome)
**Analysis Code:** E50004
**Related Tasks:** E5-003 (Change Order Branch Versioning)

---

## User Story

**As a** project manager working on a change order branch
**I want to** see the full project context (all entities from main branch) alongside branch-specific changes
**So that** I can understand the complete impact of my changes, see what remains unchanged, and delete entities that exist in main but not in my branch.

### Problem Statement

**Current Behavior:**
When a user selects a change order branch (e.g., "co-001"), the system filters all queries to show only entities that exist in that branch. This creates several UX problems:

1. **Limited Visibility:** Users cannot see the full project structure - only entities that have been explicitly created or modified in the branch
2. **No Context:** Users cannot understand what remains unchanged from main branch
3. **Cannot Delete:** Users cannot delete entities that exist in main but haven't been touched in the branch (they don't appear in branch-only view)
4. **Impact Assessment:** Users cannot assess the full impact of changes because they can't see the baseline (main branch state)

**Example Scenario:**
- Main branch has 10 WBEs and 50 cost elements
- Change order branch "co-001" modifies 2 WBEs and creates 1 new cost element
- Current view shows only 2 WBEs (modified) and 1 cost element (new) = 3 total entities
- User cannot see the other 8 unchanged WBEs or 49 unchanged cost elements
- User cannot delete any of the 8 unchanged WBEs from within the branch view

---

## 1. CODEBASE PATTERN ANALYSIS

### Existing Display Patterns

1. **Branch Comparison View (Separate Component)**
   - Location: `frontend/src/components/Projects/BranchComparisonView.tsx`
   - Pattern: Side-by-side comparison showing creates/updates/deletes
   - API: `backend/app/api/routes/branch_comparison.py` - `compare_branches()` endpoint
   - **Limitation:** Only shows differences, not full merged view
   - **Usage:** Currently used in merge dialogs and change order detail views, not in main project views

2. **Branch Filtering Service (Backend)**
   - Location: `backend/app/services/branch_filtering.py`
   - Pattern: `apply_branch_filters()` function filters queries by branch and status
   - **Current Behavior:** Strict filtering - only returns entities from specified branch
   - **Usage:** Applied in all WBE and CostElement CRUD endpoints

3. **DataTable Component Pattern**
   - Location: `frontend/src/components/DataTable/DataTable.tsx`
   - Pattern: Reusable table component with column definitions
   - **Usage:** Used in WBEsTable, CostElementsTable, ChangeOrdersTable
   - **Capability:** Supports custom cell renderers, row actions, visual indicators

4. **Time Machine Context Pattern**
   - Location: `frontend/src/context/TimeMachineContext.tsx`
   - Pattern: Context provider for control date filtering
   - **Similarity:** Similar pattern could be used for branch display mode (branch-only vs merged)

5. **Budget Timeline Multi-Dataset Pattern**
   - Location: `frontend/src/components/Projects/BudgetTimeline.tsx`
   - Pattern: Displays multiple datasets (budget, costs, EV) on same chart
   - **Relevance:** Shows pattern for displaying multiple data sources in single view

### Architectural Layers to Respect

- **Frontend Query Layer:** TanStack Query with branch parameter in query keys
- **Backend API Layer:** FastAPI routes with branch query parameter filtering
- **Service Layer:** `branch_filtering.py` service for query scoping
- **Model Layer:** BranchVersionMixin with branch field for WBE/CostElement
- **UI Component Layer:** Chakra UI components with DataTable pattern

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### Backend Dependencies/Config

**New API Endpoints Needed:**
- `GET /api/wbes/merged-view` - Returns merged view (main + branch entities)
- `GET /api/cost-elements/merged-view` - Returns merged view for cost elements
- Alternative: Extend existing endpoints with `view_mode` parameter: `branch-only` | `merged` | `main-only`

**Service Layer Modifications:**
- `backend/app/services/branch_filtering.py` - Add `get_merged_entities()` function
- Function should:
  - Fetch all active entities from main branch
  - Fetch all active entities from specified branch
  - Merge results with branch entities taking precedence
  - Mark entities with change indicators (created, updated, deleted, unchanged)

**Query Strategy:**
- **Option A:** Single query with UNION and CASE statements
- **Option B:** Two separate queries (main + branch) merged in Python
- **Option C:** New database view/materialized view for merged branch state

**Performance Considerations:**
- Merged view queries will be more expensive (fetching from two branches)
- May need caching for merged views
- Consider pagination for large projects

### Frontend Touchpoints

**Component Modifications:**
- `frontend/src/routes/_layout/projects.$id.tsx` - WBEsTable component
- `frontend/src/routes/_layout/projects.$id.wbes.$wbeId.tsx` - CostElementsTable component
- `frontend/src/components/Projects/BranchSelector.tsx` - Add view mode toggle

**New Components:**
- `frontend/src/components/Projects/BranchViewModeToggle.tsx` - Toggle between branch-only and merged view
- `frontend/src/components/Projects/EntityChangeIndicator.tsx` - Visual indicator for entity change status
- `frontend/src/components/Projects/MergedViewDataTable.tsx` - Enhanced DataTable with change indicators

**Context/State Management:**
- Extend `BranchContext` to include `viewMode: 'branch-only' | 'merged'`
- Or create new `BranchViewContext` for view mode state

**Query Key Strategy:**
- Current: `["wbes", { projectId, page }, controlDate, branch]`
- New: `["wbes", { projectId, page }, controlDate, branch, viewMode]`
- Invalidate queries when view mode changes

**Visual Indicators:**
- **Created in branch:** Green border/background, "+" icon
- **Updated in branch:** Yellow border/background, "~" icon
- **Deleted in branch:** Red strikethrough, "×" icon
- **Unchanged:** Default styling, no indicator
- **Missing from branch (main only):** Grayed out, "main" badge

---

## 3. ABSTRACTION INVENTORY

### Existing Abstractions to Leverage

1. **Branch Filtering Service**
   - `apply_branch_filters()` - Can be extended or wrapped
   - `get_branch_context()` - Already provides branch context
   - **Extension:** Add `get_merged_branch_entities()` function

2. **DataTable Component**
   - Supports custom cell renderers via `cell` property
   - Supports row actions and custom styling
   - **Extension:** Add change indicator column or integrate into existing cells

3. **Branch Comparison Service**
   - `compare_branches()` API already identifies creates/updates/deletes
   - **Reuse:** Can use comparison logic to mark entities in merged view

4. **Query Options Pattern**
   - `getWBEsQueryOptions()` function pattern
   - **Extension:** Add `viewMode` parameter to query options

5. **Context Provider Pattern**
   - `BranchProvider` and `useBranch()` hook
   - **Extension:** Add view mode to context or create separate provider

### Patterns for Implementation

- **Merged Query Pattern:**
  - Fetch main branch entities (all active)
  - Fetch branch entities (all active)
  - Merge in Python/TypeScript with branch entities overriding main
  - Mark entities with change status from comparison API

- **Visual Indicator Pattern:**
  - Add optional `changeStatus` field to entity types
  - Use Chakra UI Badge/Icon components for indicators
  - Conditional styling based on change status

- **View Mode Toggle Pattern:**
  - Similar to time machine control date picker
  - Radio buttons or toggle switch: "Branch Only" | "Merged View"
  - Persist preference in localStorage (per project)

---

## 4. ALTERNATIVE APPROACHES

| Approach | Summary | Pros | Cons/Risks | Architectural Alignment | Complexity |
| --- | --- | --- | --- | --- | --- |
| **A. Merged View with Visual Indicators (Recommended)** | Show all main branch entities + branch entities merged, with visual indicators for change status. Toggle between "branch-only" and "merged" view modes. | Full project context visible; Clear visual distinction of changes; Can delete any entity; Understands full impact; Maintains existing branch-only mode. | More complex queries (fetch from 2 branches); Visual clutter if many entities; Performance impact; Need to merge data client/server side. | High - Extends existing patterns; Uses DataTable component; Follows context provider pattern. | Medium-High (backend merged query + frontend indicators) |
| **B. Side-by-Side Split View** | Split screen showing main branch on left, branch on right, with diff highlighting. | Clear visual separation; Easy to compare; Shows all data. | Takes more screen space; Complex layout; Harder to interact (which side to edit?); Mobile unfriendly. | Medium - Requires new layout component; Different from existing patterns. | High (new layout + diff logic) |
| **C. Overlay/Modal Comparison** | Keep branch-only view, add "Compare with Main" button that opens overlay showing full comparison. | Minimal changes to existing code; Branch-only remains default; Comparison on demand. | Doesn't solve core problem (still can't see full context in main view); Requires modal navigation; Doesn't allow deleting unchanged entities. | Low - Minimal changes; Uses existing BranchComparisonView. | Low (reuse existing comparison) |
| **D. Expandable Rows with Main Context** | Show branch entities by default, with expandable rows showing "main branch context" for each entity. | Compact default view; Context available on demand; Progressive disclosure. | Doesn't show unchanged entities; Still can't delete main-only entities; Requires expansion to see context. | Medium - Extends DataTable with expandable rows. | Medium (expandable row pattern) |
| **E. Dual-Mode Tabs** | Add tabs: "Branch View" (current) and "Merged View" (new). | Clear separation of modes; Easy to switch; No visual clutter in branch view. | Requires tab navigation; Context switching overhead; May feel disconnected. | Medium - Uses existing tab pattern. | Medium (new tab + merged view) |

### Recommended Approach: **A. Merged View with Visual Indicators**

**Rationale:**
- Solves all identified problems (visibility, context, deletion, impact assessment)
- Maintains backward compatibility (branch-only mode still available)
- Follows existing architectural patterns (DataTable, context providers, query patterns)
- Provides best user experience (full context without navigation)
- Can be implemented incrementally (start with merged view, add indicators)

**Implementation Strategy:**
1. Add `viewMode` parameter to backend endpoints (default: "branch-only" for backward compatibility)
2. Create merged query service function
3. Add view mode toggle to BranchSelector component
4. Enhance DataTable with change indicators
5. Update query keys to include viewMode
6. Add visual styling for change indicators

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### Principles Upheld

- **Architectural Respect:** Extends existing patterns (branch filtering, DataTable, context providers)
- **Incremental Change:** Can be implemented as optional feature (default to branch-only)
- **Test-Driven Development:** Merged view queries can be tested with failing tests first
- **No Code Duplication:** Reuses existing branch comparison logic and DataTable component

### Potential Violations

- **Query Complexity:** Merged queries are more expensive (fetching from 2 branches)
- **Performance:** May impact page load times for large projects
- **State Management:** Additional state (viewMode) to manage and sync
- **Visual Complexity:** More visual indicators may clutter interface

### Future Maintenance

- **Query Optimization:** May need database indexes or materialized views for performance
- **Caching Strategy:** Consider caching merged views to reduce query load
- **Mobile Responsiveness:** Ensure visual indicators work on small screens
- **Accessibility:** Ensure change indicators are accessible (screen readers, color blind)

### Testing Challenges

- **Merged View Tests:** Test that merged view correctly combines main + branch entities
- **Change Indicator Tests:** Test that indicators correctly reflect entity status
- **Performance Tests:** Test query performance with large datasets
- **UI Tests:** Test view mode toggle and visual indicators
- **Edge Cases:** Test with empty branches, deleted entities, concurrent modifications

---

## Risks, Unknowns, and Ambiguities

### Data Semantics (TO BE CONFIRMED)

- **Entity Merging Strategy:** ✅ **PROPOSED** - Branch entities override main entities for same entity_id
- **Change Status Calculation:** ⚠️ **TO CONFIRM** - Use branch comparison API or calculate inline?
- **Deleted Entity Display:** ⚠️ **TO CONFIRM** - Show deleted entities in merged view? (probably yes, with strikethrough)
- **Version Selection:** ⚠️ **TO CONFIRM** - Which version to show in merged view? (latest active version per branch)

### Implementation Details (TO BE CONFIRMED)

- **View Mode Default:** ⚠️ **TO CONFIRM** - Default to "branch-only" (backward compatible) or "merged"?
- **Performance Threshold:** ⚠️ **TO CONFIRM** - At what entity count should we warn about performance or paginate?
- **Caching Strategy:** ⚠️ **TO CONFIRM** - Cache merged views? For how long? When to invalidate?
- **Mobile Experience:** ⚠️ **TO CONFIRM** - How to handle merged view on mobile? (Simplified indicators?)

### Business Rules (TO BE CONFIRMED)

- **Delete Behavior:** ⚠️ **TO CONFIRM** - When deleting entity in merged view, should it:
  - Create delete in branch (soft delete in branch)?
  - Only work for entities that exist in branch?
  - Allow deleting main-only entities (creates delete marker in branch)?
- **Edit Behavior:** ⚠️ **TO CONFIRM** - When editing entity in merged view:
  - If entity exists in branch, edit branch version
  - If entity only exists in main, create new version in branch?
- **Create Behavior:** ✅ **CONFIRMED** - New entities always created in current branch

---

## Summary & Next Steps

- **What:** Enhance branch display to show full project context (main branch entities) alongside branch-specific changes, with visual indicators for change status. Add toggle between "branch-only" and "merged" view modes.

- **Why:** Solves UX problems where users cannot see full project context, understand impact of changes, or delete unchanged entities when working in a change order branch.

- **Recommended Approach:** Merged View with Visual Indicators (Approach A)
  - Backend: Add `viewMode` parameter to WBE/CostElement endpoints
  - Backend: Create merged query service function
  - Frontend: Add view mode toggle to BranchSelector
  - Frontend: Enhance DataTable with change indicators
  - Visual indicators: Green (created), Yellow (updated), Red (deleted), Gray (main-only)

- **Next Steps:**
  1. ⏳ Confirm data semantics and business rules (entity merging, delete behavior, etc.)
  2. ⏳ Design visual indicator system (icons, colors, badges)
  3. ⏳ Create failing tests for merged view queries
  4. ⏳ Implement backend merged query service
  5. ⏳ Add viewMode parameter to API endpoints
  6. ⏳ Implement frontend view mode toggle
  7. ⏳ Add change indicators to DataTable
  8. ⏳ Test performance with large datasets
  9. ⏳ Add caching if needed

---

## UI EXPERIENCE DESCRIPTION

### Merged View Experience

**Scenario: User working in change order branch "co-001"**

**Step 1: Switch to Merged View**
- User is viewing WBEs in branch "co-001" (branch-only mode)
- Sees only 2 WBEs (modified in branch)
- Clicks "View Mode" toggle: "Branch Only" → "Merged View"
- Page refreshes, now shows all 10 WBEs from main branch

**Step 2: Visual Indicators**
- **WBE 1 (Modified):** Yellow border, "Modified" badge, shows branch values
- **WBE 2 (Modified):** Yellow border, "Modified" badge, shows branch values
- **WBE 3-10 (Unchanged):** Default styling, no indicator, shows main branch values
- **WBE 11 (New in branch):** Green border, "New" badge, shows branch values

**Step 3: Understanding Impact**
- User can see all 10 original WBEs + 1 new WBE
- User understands that only 2 WBEs were modified, 8 remain unchanged
- User can assess financial impact: see original values vs modified values

**Step 4: Delete Unchanged Entity**
- User wants to delete WBE 5 (unchanged, exists only in main)
- Clicks delete on WBE 5
- System creates delete marker in branch (soft delete)
- WBE 5 now shows with red strikethrough and "Deleted" badge
- After merge, WBE 5 will be deleted in main branch

**Step 5: Edit Unchanged Entity**
- User wants to modify WBE 6 (unchanged, exists only in main)
- Clicks edit on WBE 6
- System creates new version in branch with user's changes
- WBE 6 now shows with yellow border and "Modified" badge
- Shows branch values (modified) with option to see original main values

---

## REAL-WORLD EXAMPLES

### Example 1: Merged View for WBE List

**Main Branch State:**
- 10 WBEs (WBE-1 through WBE-10)
- All active, total revenue: €1,000,000

**Branch "co-001" State:**
- Modified WBE-2 (revenue changed from €100,000 to €150,000)
- Created WBE-11 (new, revenue: €50,000)
- Deleted WBE-5 (soft delete in branch)

**Merged View Display:**
```
WBE-1   [Machine A]    €100,000  [Unchanged]
WBE-2   [Machine B]    €150,000  [Modified] 🟡
WBE-3   [Machine C]    €80,000   [Unchanged]
WBE-4   [Machine D]    €120,000  [Unchanged]
WBE-5   [Machine E]    €90,000   [Deleted] 🔴
WBE-6   [Machine F]    €110,000  [Unchanged]
WBE-7   [Machine G]    €95,000   [Unchanged]
WBE-8   [Machine H]    €105,000  [Unchanged]
WBE-9   [Machine I]    €100,000  [Unchanged]
WBE-10  [Machine J]    €100,000  [Unchanged]
WBE-11  [Machine K]    €50,000   [New] 🟢
```

**User Benefits:**
- Sees all 11 WBEs (10 original + 1 new)
- Understands that only WBE-2 was modified, WBE-5 will be deleted
- Can delete any of the unchanged WBEs if needed
- Can assess total impact: €1,050,000 (was €1,000,000, +€50,000 from new, +€50,000 from WBE-2 increase, -€90,000 from WBE-5 deletion = net +€10,000)

---

## DATABASE CHANGES SUMMARY

### No Schema Changes Required

- Existing branch/version/status columns are sufficient
- Merged view is a query-time operation, not a storage change

### Query Changes

**New Merged Query Pattern:**
```python
def get_merged_wbes(project_id: UUID, branch: str) -> list[WBE]:
    # Get all active WBEs from main branch
    main_wbes = session.exec(
        apply_branch_filters(
            select(WBE).where(WBE.project_id == project_id),
            WBE,
            branch="main",
            include_deleted=False,
        )
    ).all()

    # Get all active WBEs from branch
    branch_wbes = session.exec(
        apply_branch_filters(
            select(WBE).where(WBE.project_id == project_id),
            WBE,
            branch=branch,
            include_deleted=False,
        )
    ).all()

    # Create maps
    main_map = {wbe.entity_id: wbe for wbe in main_wbes}
    branch_map = {wbe.entity_id: wbe for wbe in branch_wbes}

    # Merge: branch entities override main, mark change status
    merged = []
    for entity_id, main_wbe in main_map.items():
        branch_wbe = branch_map.get(entity_id)
        if branch_wbe:
            # Exists in both - use branch version (updated)
            merged.append((branch_wbe, "updated"))
        else:
            # Only in main - check if deleted in branch
            deleted_in_branch = session.exec(
                select(WBE)
                .where(WBE.entity_id == entity_id)
                .where(WBE.branch == branch)
                .where(WBE.status == "deleted")
            ).first()
            if deleted_in_branch:
                merged.append((main_wbe, "deleted"))
            else:
                merged.append((main_wbe, "unchanged"))

    # Add branch-only entities (created)
    for entity_id, branch_wbe in branch_map.items():
        if entity_id not in main_map:
            merged.append((branch_wbe, "created"))

    return merged
```

---

**Next Steps:**
1. Review and confirm this analysis
2. Confirm data semantics and business rules
3. Proceed to detailed implementation plan
