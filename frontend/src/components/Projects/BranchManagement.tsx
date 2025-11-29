import { Badge, Box, Flex, Heading, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { ChangeOrdersService, OpenAPI } from "@/client"
import { DataTable } from "@/components/DataTable/DataTable"
import type { ColumnDefExtended } from "@/components/DataTable/types"
import { useBranch } from "@/context/BranchContext"
import LockBranch from "./LockBranch"
import UnlockBranch from "./UnlockBranch"

interface BranchManagementProps {
  projectId: string
}

interface BranchLockInfo {
  lock_id: string
  project_id: string
  branch: string
  locked_by_id: string
  locked_by_name: string | null
  reason: string | null
  locked_at: string
}

interface BranchLocksResponse {
  locks: Record<string, BranchLockInfo>
}

const BranchManagement = ({ projectId }: BranchManagementProps) => {
  const { availableBranches } = useBranch()

  const { data: changeOrders, isLoading: isLoadingChangeOrders } = useQuery({
    queryKey: ["change-orders", projectId],
    queryFn: () =>
      ChangeOrdersService.listChangeOrders({
        projectId,
        skip: 0,
        limit: 1000,
      }),
    enabled: !!projectId,
  })

  const { data: locksData, isLoading: isLoadingLocks } =
    useQuery<BranchLocksResponse>({
      queryKey: ["branch-locks", projectId],
      queryFn: async () => {
        const apiBase =
          OpenAPI.BASE ||
          window.env?.VITE_API_URL ||
          import.meta.env.VITE_API_URL ||
          "http://localhost:8010"
        const token = localStorage.getItem("access_token") || ""
        const response = await fetch(
          `${apiBase}/api/v1/projects/${projectId}/branches/locks`,
          {
            headers: {
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
          },
        )
        if (!response.ok) {
          throw new Error("Failed to fetch branch locks")
        }
        return response.json()
      },
      enabled: !!projectId,
    })

  // Create branch data from change orders and lock status
  const branchData = availableBranches.map((branch) => {
    const changeOrder = changeOrders?.find((co) => co.branch === branch)
    const lockInfo = locksData?.locks[branch]
    return {
      branch,
      changeOrderNumber: changeOrder?.change_order_number || "N/A",
      status: changeOrder?.workflow_status || "N/A",
      title: changeOrder?.title || "N/A",
      isLocked: !!lockInfo,
      lockInfo: lockInfo || null,
    }
  })

  const isLoading = isLoadingChangeOrders || isLoadingLocks

  const columns: ColumnDefExtended<(typeof branchData)[0]>[] = [
    {
      accessorKey: "branch",
      header: "Branch",
      enableSorting: true,
      size: 150,
      defaultVisible: true,
    },
    {
      accessorKey: "changeOrderNumber",
      header: "Change Order",
      enableSorting: true,
      size: 150,
      defaultVisible: true,
    },
    {
      accessorKey: "title",
      header: "Title",
      enableSorting: true,
      size: 200,
      defaultVisible: true,
    },
    {
      accessorKey: "status",
      header: "Status",
      enableSorting: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => (
        <span style={{ textTransform: "capitalize" }}>
          {String(getValue())}
        </span>
      ),
    },
    {
      accessorKey: "isLocked",
      header: "Lock Status",
      enableSorting: true,
      size: 200,
      defaultVisible: true,
      cell: ({ row }) => {
        const isLocked = row.original.isLocked
        const lockInfo = row.original.lockInfo
        if (!isLocked) {
          return <Badge colorPalette="gray">Unlocked</Badge>
        }
        return (
          <Box>
            <Badge colorPalette="orange" mb={1}>
              Locked
            </Badge>
            {lockInfo?.locked_by_name && (
              <Text fontSize="xs" color="fg.muted">
                by {lockInfo.locked_by_name}
              </Text>
            )}
            {lockInfo?.reason && (
              <Text fontSize="xs" color="fg.muted" title={lockInfo.reason}>
                {lockInfo.reason.length > 30
                  ? `${lockInfo.reason.substring(0, 30)}...`
                  : lockInfo.reason}
              </Text>
            )}
          </Box>
        )
      },
    },
    {
      id: "actions",
      header: "Actions",
      enableSorting: false,
      enableResizing: false,
      enableColumnFilter: false,
      size: 120,
      defaultVisible: true,
      cell: ({ row }) => (
        <Flex gap={2}>
          <LockBranch
            projectId={projectId}
            branch={row.original.branch}
            isLocked={row.original.isLocked}
          />
          <UnlockBranch
            projectId={projectId}
            branch={row.original.branch}
            isLocked={row.original.isLocked}
          />
        </Flex>
      ),
    },
  ]

  return (
    <Box p={4}>
      <Heading size="md" mb={4}>
        Branch Management
      </Heading>
      <DataTable
        data={branchData}
        columns={columns}
        tableId="branch-management-table"
        isLoading={isLoading}
        count={branchData.length}
        page={1}
        onPageChange={() => {}}
        pageSize={branchData.length}
      />
    </Box>
  )
}

export default BranchManagement
