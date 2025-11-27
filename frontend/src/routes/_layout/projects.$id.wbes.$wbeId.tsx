import {
  Box,
  Container,
  EmptyState,
  Flex,
  Heading,
  Tabs,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import {
  createFileRoute,
  Link,
  Outlet,
  useNavigate,
  useRouterState,
} from "@tanstack/react-router"
import { useState } from "react"
import { FiChevronRight, FiTag } from "react-icons/fi"
import { z } from "zod"
import type { CostElementPublic, CostElementWithSchedulePublic } from "@/client"
import {
  BudgetTimelineService,
  CostElementsService,
  ProjectsService,
  WbesService,
} from "@/client"
import { DataTable } from "@/components/DataTable/DataTable"
import type { ColumnDefExtended } from "@/components/DataTable/types"
import PendingItems from "@/components/Pending/PendingItems"
import AddCostElement from "@/components/Projects/AddCostElement"
import AIChat from "@/components/Projects/AIChat"
import BranchSelector from "@/components/Projects/BranchSelector"
import BudgetTimeline from "@/components/Projects/BudgetTimeline"
import BudgetTimelineFilter from "@/components/Projects/BudgetTimelineFilter"
import { ChangeStatusIndicator } from "@/components/Projects/ChangeStatusIndicator"
import DeleteCostElement from "@/components/Projects/DeleteCostElement"
import EditCostElement from "@/components/Projects/EditCostElement"
import MetricsSummary from "@/components/Projects/MetricsSummary"
import { BranchProvider, useBranch } from "@/context/BranchContext"
import { useTimeMachine } from "@/context/TimeMachineContext"
import type { CostElementView } from "./projects.$id.wbes.$wbeId.cost-elements.$costElementId"

const WBE_TAB_OPTIONS = [
  "info",
  "cost-elements",
  "summary",
  "cost-summary",
  "metrics",
  "timeline",
  "ai-assessment",
] as const

type WbeDetailTab = (typeof WBE_TAB_OPTIONS)[number]

const wbeDetailSearchSchema = z.object({
  page: z.number().catch(1),
  tab: z.enum(WBE_TAB_OPTIONS).catch("cost-elements"),
})

const PER_PAGE = 10
const COST_ELEMENT_DETAIL_DEFAULT_VIEW: CostElementView = "cost-registrations"

function getProjectQueryOptions({
  id,
  controlDate,
}: {
  id: string
  controlDate: string
}) {
  return {
    queryFn: () => ProjectsService.readProject({ id }),
    queryKey: ["projects", id, controlDate],
  }
}

function getWBEQueryOptions({
  id,
  controlDate,
  branch,
}: {
  id: string
  controlDate: string
  branch: string
}) {
  return {
    // TODO: After client regeneration, use readWbeByEntityId with entity_id
    // For now, using primary key endpoint for URL compatibility
    queryFn: () => WbesService.readWbe({ id, branch: branch || "main" }),
    queryKey: ["wbes", id, controlDate, branch],
  }
}

function getCostElementsQueryOptions({
  wbeId,
  page,
  controlDate,
  branch,
  viewMode,
}: {
  wbeId: string
  page: number
  controlDate: string
  branch: string
  viewMode: "merged" | "branch-only"
}) {
  return {
    queryFn: () =>
      CostElementsService.readCostElements({
        wbeId: wbeId,
        skip: (page - 1) * PER_PAGE,
        limit: PER_PAGE,
        branch: branch || "main",
        viewMode: viewMode,
      }),
    queryKey: [
      "cost-elements",
      { wbeId: wbeId, page },
      controlDate,
      branch,
      viewMode,
    ],
  }
}

export const Route = createFileRoute("/_layout/projects/$id/wbes/$wbeId")({
  component: WBEDetail,
  validateSearch: (search) => wbeDetailSearchSchema.parse(search),
})

// Function to get column definitions for Cost Elements table
function getCostElementsColumns(
  viewMode: "merged" | "branch-only",
): ColumnDefExtended<CostElementPublic>[] {
  const columns: ColumnDefExtended<CostElementPublic>[] = [
    {
      accessorKey: "department_name",
      header: "Department",
      enableSorting: true,
      enableResizing: true,
      enableColumnFilter: true,
      filterType: "text",
      size: 200,
      defaultVisible: true,
      cell: ({ row, getValue }) => {
        const value = getValue() as string
        const isDeleted =
          viewMode === "merged" && row.original.change_status === "deleted"
        return (
          <Text
            textDecoration={isDeleted ? "line-through" : "none"}
            color={isDeleted ? "gray.500" : "inherit"}
          >
            {value}
          </Text>
        )
      },
    },
    {
      accessorKey: "department_code",
      header: "Department Code",
      enableSorting: true,
      enableResizing: true,
      enableColumnFilter: true,
      filterType: "text",
      size: 150,
      defaultVisible: true,
    },
    {
      accessorKey: "status",
      header: "Status",
      enableSorting: true,
      enableResizing: true,
      enableColumnFilter: true,
      filterType: "select",
      filterConfig: {
        type: "select",
        options: ["planned", "in-progress", "completed", "on-hold"],
      },
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => (
        <span style={{ textTransform: "capitalize" }}>
          {(getValue() as string) || "planned"}
        </span>
      ),
    },
    {
      accessorKey: "budget_bac",
      header: "Budget (BAC)",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => (getValue() as string) || "0.00",
    },
    {
      accessorKey: "revenue_plan",
      header: "Revenue Plan",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => (getValue() as string) || "0.00",
    },
  ]

  // Add change status column when in merged view
  if (viewMode === "merged") {
    columns.splice(2, 0, {
      accessorKey: "change_status",
      header: "Change Status",
      enableSorting: true,
      enableResizing: true,
      enableColumnFilter: true,
      filterType: "select",
      filterConfig: {
        type: "select",
        options: ["created", "updated", "deleted", "unchanged"],
      },
      size: 120,
      defaultVisible: true,
      cell: ({ row }) => {
        const changeStatus = row.original.change_status
        if (!changeStatus) return null
        return (
          <ChangeStatusIndicator
            changeStatus={
              changeStatus as "created" | "updated" | "deleted" | "unchanged"
            }
          />
        )
      },
    })
  }

  columns.push({
    id: "actions",
    header: "Actions",
    enableSorting: false,
    enableColumnFilter: false,
    size: 120,
    defaultVisible: true,
    cell: ({ row }) => (
      <Flex gap={2}>
        <EditCostElement costElement={row.original} />
        <DeleteCostElement
          costElement={row.original}
          departmentName={row.original.department_name}
        />
      </Flex>
    ),
  })

  return columns
}

function CostElementsTable({ wbeId }: { wbeId: string }) {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()
  const { controlDate } = useTimeMachine()
  const { currentBranch, viewMode } = useBranch()

  const { data, isLoading } = useQuery({
    ...getCostElementsQueryOptions({
      wbeId,
      page,
      controlDate,
      branch: currentBranch,
      viewMode,
    }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      search: (prev) => ({ ...prev, page }),
    })
  }

  const costElements = data?.data ?? []
  const count = data?.count ?? 0

  const { id: projectId } = Route.useParams()

  const handleRowClick = (costElement: CostElementPublic) => {
    navigate({
      to: "/projects/$id/wbes/$wbeId/cost-elements/$costElementId",
      params: {
        id: projectId,
        wbeId: wbeId,
        costElementId: costElement.cost_element_id,
      },
      search: (prev) => ({
        ...prev,
        view: COST_ELEMENT_DETAIL_DEFAULT_VIEW,
      }),
    })
  }

  if (!isLoading && costElements.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiTag />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>No cost elements found</EmptyState.Title>
            <EmptyState.Description>
              This WBE has no cost elements yet
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  const columns = getCostElementsColumns(viewMode)

  return (
    <DataTable
      data={costElements}
      columns={columns}
      tableId="cost-elements-table"
      onRowClick={handleRowClick}
      isLoading={isLoading}
      count={count}
      page={page}
      onPageChange={setPage}
      pageSize={PER_PAGE}
    />
  )
}

function WBEDetailContent({
  projectId,
  wbeId,
}: {
  projectId: string
  wbeId: string
}) {
  const navigate = useNavigate({ from: Route.fullPath })
  const { tab } = Route.useSearch()
  const { controlDate } = useTimeMachine()
  const mappedTab =
    tab === "summary" || tab === "cost-summary" ? "metrics" : tab

  const { data: project } = useQuery({
    ...getProjectQueryOptions({ id: projectId, controlDate }),
  })

  const { currentBranch } = useBranch()
  const { data: wbe } = useQuery({
    ...getWBEQueryOptions({ id: wbeId, controlDate, branch: currentBranch }),
  })

  // Budget Timeline state - persists across tab switches
  // Pre-select current WBE by default
  const [filter, setFilter] = useState<{
    wbeIds?: string[]
    costElementIds?: string[]
    costElementTypeIds?: string[]
  }>({
    wbeIds: [wbeId],
  })
  // Fetch cost elements with schedules based on filter
  // Normalize filter arrays for consistent query key comparison
  const normalizedFilter = {
    wbeIds: filter.wbeIds?.length ? [...filter.wbeIds].sort() : undefined,
    costElementIds: filter.costElementIds?.length
      ? [...filter.costElementIds].sort()
      : undefined,
    costElementTypeIds: filter.costElementTypeIds?.length
      ? [...filter.costElementTypeIds].sort()
      : undefined,
  }

  const { data: costElements, isLoading: isLoadingCostElements } = useQuery<
    CostElementWithSchedulePublic[]
  >({
    queryFn: () =>
      BudgetTimelineService.getCostElementsWithSchedules({
        projectId: projectId,
        wbeIds: normalizedFilter.wbeIds,
        costElementIds: normalizedFilter.costElementIds,
        costElementTypeIds: normalizedFilter.costElementTypeIds,
      }),
    queryKey: [
      "cost-elements-with-schedules",
      projectId,
      normalizedFilter.wbeIds,
      normalizedFilter.costElementIds,
      normalizedFilter.costElementTypeIds,
      controlDate,
    ],
    enabled: !!projectId && !!wbeId,
  })

  const handleFilterChange = (newFilter: {
    wbeIds?: string[]
    costElementIds?: string[]
    costElementTypeIds?: string[]
  }) => {
    setFilter(newFilter)
  }

  const handleTabChange = (value: WbeDetailTab) => {
    navigate({
      search: (prev) =>
        ({
          ...prev,
          tab: value,
        }) as typeof prev,
    })
  }

  if (!project || !wbe) {
    return (
      <Container maxW="full">
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Title>Project or WBE not found</EmptyState.Title>
          </EmptyState.Content>
        </EmptyState.Root>
      </Container>
    )
  }

  return (
    <Container maxW="full">
      <Flex alignItems="center" gap={2} pt={12} mb={2}>
        <Link to="/projects" search={{ page: 1 }}>
          <Text
            fontSize="sm"
            color="blue.500"
            _hover={{ textDecoration: "underline" }}
          >
            Projects
          </Text>
        </Link>
        <FiChevronRight />
        <Link
          to="/projects/$id"
          params={{ id: project.project_id }}
          search={{ page: 1, tab: "wbes" } as any}
        >
          <Text
            fontSize="sm"
            color="blue.500"
            _hover={{ textDecoration: "underline" }}
          >
            {project.project_name}
          </Text>
        </Link>
        <FiChevronRight />
        <Text fontSize="sm" color="gray.600">
          {wbe.machine_type}
        </Text>
      </Flex>
      <Flex alignItems="center" justifyContent="space-between" mb={4}>
        <Heading size="lg">
          {project.project_name} - {wbe.machine_type}
        </Heading>
        <BranchSelector projectId={projectId} />
      </Flex>

      <Tabs.Root
        value={mappedTab}
        onValueChange={({ value }) => handleTabChange(value as WbeDetailTab)}
        variant="subtle"
        mt={4}
      >
        <Tabs.List>
          <Tabs.Trigger value="info">WBE Information</Tabs.Trigger>
          <Tabs.Trigger value="cost-elements">Cost Elements</Tabs.Trigger>
          <Tabs.Trigger value="metrics">Metrics</Tabs.Trigger>
          <Tabs.Trigger value="timeline">Budget Timeline</Tabs.Trigger>
          <Tabs.Trigger value="ai-assessment">AI Assessment</Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="info">
          <Box mt={4}>
            <Text color="fg.muted">
              WBE information content will be added here.
            </Text>
          </Box>
        </Tabs.Content>

        <Tabs.Content value="cost-elements">
          <Box mt={4}>
            <Flex alignItems="center" justifyContent="space-between" mb={4}>
              <Heading size="md">Cost Elements</Heading>
              <AddCostElement wbeId={wbe.wbe_id} />
            </Flex>
            <CostElementsTable wbeId={wbe.wbe_id} />
          </Box>
        </Tabs.Content>

        <Tabs.Content value="metrics">
          <MetricsSummary
            level="wbe"
            projectId={projectId}
            wbeId={wbe.wbe_id}
          />
        </Tabs.Content>

        <Tabs.Content value="timeline">
          <Box mt={4}>
            <Heading size="md" mb={4}>
              Budget Timeline
            </Heading>
            <BudgetTimelineFilter
              projectId={projectId}
              context="wbe"
              initialFilters={{ wbeIds: [wbeId] }}
              onFilterChange={handleFilterChange}
            />
            {isLoadingCostElements ? (
              <Box
                p={4}
                borderWidth="1px"
                borderRadius="lg"
                bg="bg.surface"
                mt={4}
              >
                <Text>Loading cost elements...</Text>
              </Box>
            ) : costElements && costElements.length === 0 ? (
              <Box
                p={4}
                borderWidth="1px"
                borderRadius="lg"
                bg="bg.surface"
                mt={4}
              >
                <Text color="fg.muted">
                  No cost elements found matching the selected filters.
                </Text>
              </Box>
            ) : (
              <Box mt={4}>
                <BudgetTimeline
                  costElements={costElements || []}
                  viewMode="aggregated"
                  projectId={projectId}
                  wbeIds={normalizedFilter.wbeIds}
                  costElementIds={normalizedFilter.costElementIds}
                />
              </Box>
            )}
          </Box>
        </Tabs.Content>

        <Tabs.Content value="ai-assessment">
          <Box mt={4} h="calc(100vh - 300px)">
            <AIChat contextType="wbe" contextId={wbe.wbe_id} />
          </Box>
        </Tabs.Content>
      </Tabs.Root>
    </Container>
  )
}

function WBEDetail() {
  const { id: projectId, wbeId } = Route.useParams()
  const location = useRouterState({
    select: (state) => state.location.pathname,
  })
  const { controlDate } = useTimeMachine()

  // Check if we're on a cost element detail route (child route)
  const isCostElementRoute = location.includes("/cost-elements/")

  const { data: project, isLoading: isLoadingProject } = useQuery({
    ...getProjectQueryOptions({ id: projectId, controlDate }),
  })

  if (isLoadingProject) {
    return (
      <Container maxW="full">
        <PendingItems />
      </Container>
    )
  }

  if (!project) {
    return (
      <Container maxW="full">
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Title>Project not found</EmptyState.Title>
          </EmptyState.Content>
        </EmptyState.Root>
      </Container>
    )
  }

  // If we're on a cost element detail route (child route), render Outlet for child route
  if (isCostElementRoute) {
    return (
      <BranchProvider projectId={projectId}>
        <Outlet />
      </BranchProvider>
    )
  }

  return (
    <BranchProvider projectId={projectId}>
      <WBEDetailContent projectId={projectId} wbeId={wbeId} />
    </BranchProvider>
  )
}
