# High-Level Analysis: Branch Locking UI Integration

**Task:** Enable branch locking functionality in the Branch Management UI
**Status:** Analysis Phase
**Date:** 2025-11-29
**Current Time:** 08:38 CET (Europe/Rome)
**Analysis Code:** 845712

---

## User Story

**As a** project manager
**I want to** lock and unlock branches directly from the Branch Management table interface
**So that** I can prevent modifications to branches during review or approval processes without navigating to a separate page.

---

## 1. CODEBASE PATTERN ANALYSIS

### Existing Implementations

1. **BranchService Lock/Unlock Methods** (`backend/app/services/branch_service.py`)
   - `lock_branch()`: Creates a BranchLock record with `project_id`, `branch`, `locked_by_id`, `reason`, `locked_at`
   - `unlock_branch()`: Removes the BranchLock record
   - `get_branch_lock()`: Retrieves lock information for a branch
   - Business rules: Cannot lock main branch, cannot lock already locked branch
   - Namespace: `BranchService` static methods

```335:366:backend/app/services/branch_service.py
    def lock_branch(
        session: Session,
        project_id: uuid.UUID,
        branch: str,
        locked_by_id: uuid.UUID,
        reason: str | None = None,
    ) -> BranchLock:
        """Create a lock entry for a branch."""
        if branch == BranchService.MAIN_BRANCH:
            raise ValueError("Cannot lock the main branch.")

        existing = BranchService.get_branch_lock(session, project_id, branch)
        if existing:
            raise ValueError("Branch is already locked.")

        lock = BranchLock(
            project_id=project_id,
            branch=branch,
            locked_by_id=locked_by_id,
            reason=reason,
        )
        session.add(lock)
        session.flush()
        return lock

    @staticmethod
    def unlock_branch(session: Session, project_id: uuid.UUID, branch: str) -> None:
        """Release a branch lock if one exists."""
        lock = BranchService.get_branch_lock(session, project_id, branch)
        if lock:
            session.delete(lock)
            session.flush()
```

2. **BranchLock Model** (`backend/app/models/branch_lock.py`)
   - Fields: `lock_id`, `project_id`, `branch`, `locked_by_id`, `reason`, `locked_at`
   - Foreign keys to `project` and `user` tables
   - Timezone-aware `locked_at` timestamp

```10:21:backend/app/models/branch_lock.py
class BranchLock(SQLModel, table=True):
    """Represents an exclusive lock for a project branch."""

    lock_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.project_id", nullable=False)
    branch: str = Field(max_length=50, nullable=False)
    locked_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    reason: str | None = Field(default=None, max_length=200)
    locked_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
```

3. **Table Action Column Pattern** (`frontend/src/components/Projects/changeOrderColumns.tsx`)
   - Actions column with `id: "actions"` pattern
   - Uses `Flex` container with action buttons
   - Action buttons stop propagation to prevent row click events
   - Examples: EditChangeOrder, DeleteChangeOrder, ViewChangeOrder components

```95:114:frontend/src/components/Projects/changeOrderColumns.tsx
    {
      id: "actions",
      header: "Actions",
      enableSorting: false,
      enableResizing: false,
      enableColumnFilter: false,
      size: 160,
      defaultVisible: true,
      cell: ({ row }) => (
        <Flex gap={2}>
          <ViewChangeOrder changeOrder={row.original} />
          <EditChangeOrder changeOrder={row.original} />
          <DeleteChangeOrder
            changeOrderId={row.original.change_order_id}
            changeOrderNumber={row.original.change_order_number}
            projectId={row.original.project_id}
          />
        </Flex>
      ),
    },
```

4. **Mutation Pattern with TanStack Query** (`frontend/src/components/Projects/BranchLocking.tsx`)
   - Uses `useMutation` for API calls
   - Manual fetch calls (not using generated client)
   - Local state management for lock status
   - Status messages via Alert component

```29:55:frontend/src/components/Projects/BranchLocking.tsx
  const lockMutation = useMutation({
    mutationFn: async (branch: string) => {
      const response = await fetch(
        `/api/v1/projects/${projectId}/branches/${branch}/lock`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: "Manual lock" }),
        },
      )
      if (!response.ok) {
        throw new Error("Failed to lock branch")
      }
    },
    onSuccess: (_, branch) => {
      setLocks((prev) => ({
        ...prev,
        [branch]: { lockedBy: "You", lockedAt: new Date().toISOString() },
      }))
      setStatusType("success")
      setStatusMessage(`Branch ${branch} locked.`)
    },
    onError: () => {
      setStatusType("error")
      setStatusMessage("Unable to lock branch. Please try again.")
    },
  })
```

### Architectural Layers

- **Models Layer**: `backend/app/models/branch_lock.py` - SQLModel table definition
- **Service Layer**: `backend/app/services/branch_service.py` - Business logic for lock operations
- **API Layer**: `backend/app/api/routes/` - HTTP endpoints (TO BE CREATED)
- **Frontend Components**: `frontend/src/components/Projects/` - React components using TanStack Query
- **Data Table Pattern**: `frontend/src/components/DataTable/` - Reusable table component with action columns

---

## 2. INTEGRATION TOUCHPOINT MAPPING

### Backend Integration Points

1. **New API Route File** (TO BE CREATED)
   - File: `backend/app/api/routes/branches.py` (or extend existing branch routes)
   - Endpoints needed:
     - `POST /api/v1/projects/{project_id}/branches/{branch}/lock` - Lock a branch
     - `DELETE /api/v1/projects/{project_id}/branches/{branch}/lock` - Unlock a branch
     - `GET /api/v1/projects/{project_id}/branches/{branch}/lock` - Get lock status (optional, for querying)

2. **Service Layer** (EXISTS)
   - `BranchService.lock_branch()` - Already implemented
   - `BranchService.unlock_branch()` - Already implemented
   - `BranchService.get_branch_lock()` - Already implemented

3. **API Router Registration** (NEEDS UPDATE)
   - File: `backend/app/api/main.py`
   - Register new branch routes router

4. **OpenAPI Client Generation** (AUTOMATIC)
   - Generated client in `frontend/src/client/`
   - Will auto-generate after API endpoints are created

### Frontend Integration Points

1. **BranchManagement Component** (`frontend/src/components/Projects/BranchManagement.tsx`)
   - Add lock status column to table
   - Add lock/unlock action buttons in actions column
   - Fetch lock status for all branches
   - Handle lock/unlock mutations with optimistic updates

2. **Generated Client** (`frontend/src/client/`)
   - Use auto-generated service methods after API endpoints are created
   - Replace manual fetch calls with typed client methods

3. **BranchContext** (`frontend/src/context/BranchContext.tsx`)
   - May need to extend to include lock status in available branches query
   - Or fetch lock status separately

4. **Query Keys**
   - Add query keys for lock status: `["branch-locks", projectId]`
   - Invalidate on lock/unlock mutations

### Configuration Patterns

- **Authentication**: Uses `CurrentUser` dependency in API routes (existing pattern)
- **Error Handling**: FastAPI HTTPException for validation errors (existing pattern)
- **Database Transactions**: Uses `SessionDep` for database access (existing pattern)

---

## 3. ABSTRACTION INVENTORY

### Existing Abstractions to Leverage

1. **BranchService Static Methods**
   - Can be called directly from API routes
   - Already handles business logic validation
   - Returns appropriate exceptions

2. **Action Column Pattern**
   - Reusable pattern from `changeOrderColumns.tsx`
   - Can create `LockBranch` and `UnlockBranch` components following same pattern
   - Components should accept `branch`, `projectId`, and optional `lockInfo` props

3. **Mutation Hooks Pattern**
   - TanStack Query `useMutation` for API calls
   - Query invalidation pattern: `queryClient.invalidateQueries({ queryKey: ["branch-locks", projectId] })`
   - Optimistic updates for better UX

4. **Dialog/Confirmation Pattern**
   - Existing delete components show confirmation dialogs
   - Can follow `DeleteChangeOrder` pattern for lock/unlock confirmations
   - Optional: Show reason dialog for locking

5. **DataTable Component**
   - Supports action columns with click propagation prevention
   - Supports custom cell renderers
   - Supports loading states

### Test Utilities

- **Backend Tests**: `backend/tests/services/test_branch_locking.py` - Existing test patterns
- **Frontend Tests**: Pattern from `BranchLocking.test.tsx` - Can adapt for table actions

---

## 4. ALTERNATIVE APPROACHES

### Approach 1: Add Actions Column to BranchManagement Table (RECOMMENDED)

**Description:** Add lock/unlock buttons directly in the BranchManagement table as action buttons in each row.

**Pros:**
- ✅ Consistent with existing table patterns (ChangeOrdersTable, etc.)
- ✅ All branch operations in one place
- ✅ Minimal UI changes
- ✅ Users see lock status and can act immediately

**Cons:**
- ⚠️ Table becomes wider with additional columns
- ⚠️ Need to fetch lock status for all branches upfront

**Architecture Alignment:**
- ✅ Follows existing action column pattern
- ✅ Uses established mutation patterns
- ✅ Fits within existing BranchManagement component structure

**Complexity:** Low-Medium
- Create lock/unlock button components
- Add lock status fetching
- Add actions column to table

**Risk:** Low

---

### Approach 2: Modal/Dialog for Lock Operations

**Description:** Add "Manage Locks" button that opens a dialog/modal showing all branches with lock/unlock actions.

**Pros:**
- ✅ Keeps table cleaner
- ✅ Can show more lock details (reason, locked by, timestamp)
- ✅ Better for bulk operations

**Cons:**
- ⚠️ Extra navigation step
- ⚠️ Not as immediately visible
- ⚠️ Requires new dialog component

**Architecture Alignment:**
- ⚠️ Less consistent with existing table action patterns
- ✅ Uses existing dialog patterns

**Complexity:** Medium
- Create new dialog component
- Add button to BranchManagement
- Manage dialog state

**Risk:** Medium

---

### Approach 3: Separate Lock Status Column + Inline Lock Icon

**Description:** Add a lock status column showing locked/unlocked icon, clicking icon toggles lock state.

**Pros:**
- ✅ Very visual
- ✅ Minimal space usage
- ✅ Direct interaction

**Cons:**
- ⚠️ Less discoverable
- ⚠️ No space for lock details
- ⚠️ Accidental clicks more likely

**Architecture Alignment:**
- ✅ Fits table pattern
- ⚠️ Different from action button pattern

**Complexity:** Low
- Add status column
- Create lock icon toggle component

**Risk:** Medium (UX concerns)

---

### Recommendation: Approach 1

Approach 1 (Actions Column) is recommended because:
1. Most consistent with existing codebase patterns
2. Provides clear, discoverable actions
3. Minimal complexity increase
4. Follows established UI conventions
5. Can be extended later with more actions if needed

---

## 5. ARCHITECTURAL IMPACT ASSESSMENT

### Architectural Principles

**Follows:**
- ✅ **Separation of Concerns**: Service layer handles business logic, API layer handles HTTP contracts
- ✅ **DRY**: Reuses existing BranchService methods
- ✅ **Consistency**: Follows established table action patterns
- ✅ **Testability**: Can test backend service independently from API

**Potential Concerns:**
- ⚠️ **API Endpoint Structure**: Need to decide on RESTful endpoint structure
  - Option A: `/api/v1/projects/{project_id}/branches/{branch}/lock` (resource-based)
  - Option B: `/api/v1/branches/{branch}/lock?project_id={project_id}` (branch-focused)
  - Recommendation: Option A (consistent with existing project-scoped routes)

### Maintenance Burden

**Low Risk Areas:**
- Service layer is already tested and stable
- Frontend patterns are well-established
- No new architectural concepts introduced

**Medium Risk Areas:**
- API endpoint design needs to align with existing route patterns
- Lock status fetching needs efficient query strategy (batch vs individual)

**Future Considerations:**
- May need lock permissions/authorization checks later
- May want lock expiration/auto-unlock functionality
- May want lock notifications/audit trail

### Testing Challenges

**Backend:**
- ✅ Service layer already has tests
- ✅ Need integration tests for API endpoints
- ✅ Need to test error cases (already locked, invalid branch, etc.)

**Frontend:**
- ✅ Can follow existing component test patterns
- ✅ Need to test optimistic updates
- ✅ Need to test error handling and rollback
- ✅ Need to test query invalidation

**Integration:**
- ✅ End-to-end tests for lock/unlock workflow
- ✅ Test lock status visibility across components

---

## 6. GAPS AND AMBIGUITIES

### Known Gaps

1. **API Endpoints Missing**
   - No REST endpoints exist for lock/unlock operations
   - Need to create new route file or extend existing routes

2. **Lock Status Query Missing**
   - No efficient way to query lock status for multiple branches
   - May need batch endpoint or extend branch listing endpoint

3. **Generated Client Missing**
   - Frontend currently uses manual fetch calls in BranchLocking component
   - Need API endpoints first to generate client methods

4. **Lock Information Schema**
   - Need to decide on response format for lock status
   - Should include: `locked_by_id`, `locked_by_name`, `locked_at`, `reason`

### Ambiguities

1. **Lock Reason Requirement**
   - Is lock reason required or optional?
   - Should reason be shown in table or only in details?
   - Current service allows optional reason

2. **Lock Permission Model**
   - Who can lock/unlock branches?
   - Same user only, or project managers?
   - Currently no permission checks in service

3. **Lock Status Refresh**
   - How often should lock status be refreshed?
   - Should it be real-time (WebSocket) or polling?
   - Initial implementation likely polling/on-demand

4. **Lock UI Feedback**
   - Should lock status be visible in BranchSelector dropdown?
   - Should locked branches be disabled or just marked?
   - Currently not addressed

### Missing Information

- **User Management**: Need to understand how user names/display names are fetched for `locked_by` display
- **Performance**: How many branches per project? Affects batch query strategy
- **Audit Requirements**: Is lock/unlock action logging required?

---

## 7. RISKS AND UNKNOWNS

### Technical Risks

1. **Low Risk**: Service layer already tested, well-understood
2. **Medium Risk**: API endpoint design needs alignment review
3. **Low Risk**: Frontend patterns are established

### Business Risks

1. **Low Risk**: Feature is straightforward, aligns with user needs
2. **Medium Risk**: Permission model not defined (who can lock/unlock)
3. **Low Risk**: Performance impact likely minimal

### Unknown Factors

1. **Performance**: Number of branches per project (affects query strategy)
2. **Authorization**: Exact permission requirements for lock operations
3. **Integration**: How locks interact with change order workflow transitions (auto-lock on approve)

---

## SUMMARY

### Feature Description

Enable branch locking functionality directly from the Branch Management table interface. Users can lock/unlock branches via action buttons in the table, with lock status visible alongside branch information.

### Key Findings

- ✅ Backend service layer fully implemented and tested
- ❌ API endpoints need to be created
- ✅ Frontend patterns exist for table actions
- ✅ Component exists but not integrated into BranchManagement table
- ⚠️ Lock status query strategy needs definition

### Next Steps

1. Create API endpoints for lock/unlock operations
2. Create lock status query endpoint (batch or extend branch listing)
3. Generate OpenAPI client
4. Integrate lock actions into BranchManagement table
5. Add lock status column/indicators
6. Test end-to-end workflow

### Estimated Complexity

**Backend:** Low-Medium (2-4 hours)
- Create API route file
- Add endpoints following existing patterns
- Add tests

**Frontend:** Medium (4-6 hours)
- Create lock/unlock button components
- Add lock status fetching
- Integrate into table
- Add tests

**Total:** 6-10 hours

---

**Analysis Complete - Awaiting Feedback Before Detailed Planning**
