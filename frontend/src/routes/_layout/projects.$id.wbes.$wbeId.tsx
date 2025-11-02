import {
  Box,
  Container,
  EmptyState,
  Flex,
  Heading,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { FiChevronRight, FiTag } from "react-icons/fi"
import { z } from "zod"
import type { CostElementPublic } from "@/client"
import { CostElementsService, ProjectsService, WbesService } from "@/client"
import { DataTable } from "@/components/DataTable/DataTable"
import type { ColumnDefExtended } from "@/components/DataTable/types"
import PendingItems from "@/components/Pending/PendingItems"
import AddCostElement from "@/components/Projects/AddCostElement"
import DeleteCostElement from "@/components/Projects/DeleteCostElement"
import EditCostElement from "@/components/Projects/EditCostElement"

const wbeDetailSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 10

function getProjectQueryOptions({ id }: { id: string }) {
  return {
    queryFn: () => ProjectsService.readProject({ id }),
    queryKey: ["projects", id],
  }
}

function getWBEQueryOptions({ id }: { id: string }) {
  return {
    queryFn: () => WbesService.readWbe({ id }),
    queryKey: ["wbes", id],
  }
}

function getCostElementsQueryOptions({
  wbeId,
  page,
}: {
  wbeId: string
  page: number
}) {
  return {
    queryFn: () =>
      CostElementsService.readCostElements({
        wbeId: wbeId,
        skip: (page - 1) * PER_PAGE,
        limit: PER_PAGE,
      }),
    queryKey: ["cost-elements", { wbeId: wbeId, page }],
  }
}

export const Route = createFileRoute("/_layout/projects/$id/wbes/$wbeId")({
  component: WBEDetail,
  validateSearch: (search) => wbeDetailSearchSchema.parse(search),
})

// Column definitions for Cost Elements table
const costElementsColumns: ColumnDefExtended<CostElementPublic>[] = [
  {
    accessorKey: "department_name",
    header: "Department",
    enableSorting: true,
    enableResizing: true,
    enableColumnFilter: true,
    filterType: "text",
    size: 200,
    defaultVisible: true,
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
  {
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
          id={row.original.cost_element_id}
          departmentName={row.original.department_name}
        />
      </Flex>
    ),
  },
]

function CostElementsTable({ wbeId }: { wbeId: string }) {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading } = useQuery({
    ...getCostElementsQueryOptions({ wbeId, page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      search: (prev) => ({ ...prev, page }),
    })
  }

  const costElements = data?.data ?? []
  const count = data?.count ?? 0

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

  return (
    <DataTable
      data={costElements}
      columns={costElementsColumns}
      tableId="cost-elements-table"
      isLoading={isLoading}
      count={count}
      page={page}
      onPageChange={setPage}
      pageSize={PER_PAGE}
    />
  )
}

function WBEDetail() {
  const { id: projectId, wbeId } = Route.useParams()

  const { data: project, isLoading: isLoadingProject } = useQuery({
    ...getProjectQueryOptions({ id: projectId }),
  })

  const { data: wbe, isLoading: isLoadingWBE } = useQuery({
    ...getWBEQueryOptions({ id: wbeId }),
  })

  if (isLoadingProject || isLoadingWBE) {
    return (
      <Container maxW="full">
        <PendingItems />
      </Container>
    )
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
          search={{ page: 1 }}
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
      <Heading size="lg">
        {project.project_name} - {wbe.machine_type}
      </Heading>
      <Box mt={4}>
        <Flex alignItems="center" justifyContent="space-between" mb={4}>
          <Heading size="md">Cost Elements</Heading>
          <AddCostElement wbeId={wbe.wbe_id} />
        </Flex>
        <CostElementsTable wbeId={wbe.wbe_id} />
      </Box>
    </Container>
  )
}
