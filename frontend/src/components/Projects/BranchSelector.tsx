import { Badge, Box, Button, HStack, Text, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useMemo, useState } from "react"
import type { ChangeOrderPublic } from "@/client"
import { ChangeOrdersService, OpenAPI } from "@/client"
import { DataTable } from "@/components/DataTable/DataTable"
import type { ColumnDefExtended } from "@/components/DataTable/types"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import { useBranch } from "@/context/BranchContext"
import useCustomToast from "@/hooks/useCustomToast"
import { ViewModeToggle } from "./ViewModeToggle"

interface BranchSelectorProps {
  projectId: string
}

interface BranchData {
  branch: string
  status: string
  changeOrderNumber: string | null
  lastUpdated: string
  isLocked: boolean
  lockInfo: {
    locked_by_name: string | null
    reason: string | null
  } | null
}

const BranchSelector = ({ projectId }: BranchSelectorProps) => {
  const { currentBranch, setCurrentBranch, isLoading } = useBranch()
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false)
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null)

  // Fetch change orders to get branch statuses
  const { data: changeOrders, isLoading: isLoadingChangeOrders } = useQuery<
    ChangeOrderPublic[]
  >({
    queryFn: () =>
      ChangeOrdersService.listChangeOrders({
        projectId,
        skip: 0,
        limit: 1000,
      }),
    queryKey: ["change-orders", projectId],
    enabled: isDialogOpen && !!projectId,
  })

  // Fetch lock status for all branches
  const { data: locksData, isLoading: isLoadingLocks } = useQuery<{
    locks: Record<
      string,
      {
        lock_id: string
        project_id: string
        branch: string
        locked_by_id: string
        locked_by_name: string | null
        reason: string | null
        locked_at: string
      }
    >
  }>({
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
    queryKey: ["branch-locks", projectId],
    enabled: isDialogOpen && !!projectId,
  })

  // Create branch data with statuses, ordered by last update date
  const branchData = useMemo<BranchData[]>(() => {
    const branches: BranchData[] = []

    // Add main branch (main branch cannot be locked)
    branches.push({
      branch: "main",
      status: "active",
      changeOrderNumber: null,
      lastUpdated: new Date().toISOString(), // Main branch is always current
      isLocked: false,
      lockInfo: null,
    })

    // Add change order branches
    if (changeOrders) {
      changeOrders.forEach((co) => {
        if (co.branch && co.branch !== "main") {
          const lockInfo = locksData?.locks[co.branch]
          branches.push({
            branch: co.branch,
            status: co.workflow_status,
            changeOrderNumber: co.change_order_number,
            lastUpdated: co.created_at, // Use created_at as last updated
            isLocked: !!lockInfo,
            lockInfo: lockInfo
              ? {
                  locked_by_name: lockInfo.locked_by_name,
                  reason: lockInfo.reason,
                }
              : null,
          })
        }
      })
    }

    // Sort by last updated date (most recent first)
    return branches.sort((a, b) => {
      const dateA = new Date(a.lastUpdated).getTime()
      const dateB = new Date(b.lastUpdated).getTime()
      return dateB - dateA
    })
  }, [changeOrders, locksData])

  const branchColumns: ColumnDefExtended<BranchData>[] = [
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
      cell: ({ getValue }) => (getValue() as string | null) || "—",
    },
    {
      accessorKey: "status",
      header: "Status",
      enableSorting: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => {
        const status = (getValue() as string) || "active"
        return (
          <Badge
            colorPalette={
              status === "execute"
                ? "green"
                : status === "approve"
                  ? "blue"
                  : status === "design"
                    ? "yellow"
                    : "gray"
            }
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>
        )
      },
    },
    {
      accessorKey: "lastUpdated",
      header: "Last Updated",
      enableSorting: true,
      size: 150,
      defaultVisible: true,
      cell: ({ getValue }) => {
        const date = getValue() as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: "isLocked",
      header: "Lock Status",
      enableSorting: true,
      size: 150,
      defaultVisible: true,
      cell: ({ row }) => {
        const isLocked = row.original.isLocked
        const lockInfo = row.original.lockInfo
        if (!isLocked) {
          return <Badge colorPalette="gray">Unlocked</Badge>
        }
        return (
          <Box>
            <Badge colorPalette="orange">Locked</Badge>
            {lockInfo?.locked_by_name && (
              <Text fontSize="xs" color="fg.muted">
                by {lockInfo.locked_by_name}
              </Text>
            )}
          </Box>
        )
      },
    },
  ]

  const handleBranchSelect = (branch: BranchData) => {
    if (branch.branch === currentBranch) {
      setIsDialogOpen(false)
      return
    }
    setSelectedBranch(branch.branch)
    setIsDialogOpen(false)
    setIsConfirmDialogOpen(true)
  }

  const handleConfirmSwitch = () => {
    if (selectedBranch) {
      setCurrentBranch(selectedBranch)
      setIsConfirmDialogOpen(false)
      setSelectedBranch(null)
      // Navigate to project main page
      navigate({
        to: "/projects/$id",
        params: { id: projectId },
        search: { page: 1, tab: "wbes" } as any,
      })
    }
  }

  return (
    <>
      <HStack gap={4} align="center">
        <HStack gap={2}>
          <Text fontSize="sm" color="fg.muted">
            Branch: <strong>{currentBranch}</strong>
          </Text>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setIsDialogOpen(true)}
            disabled={isLoading}
          >
            Switch
          </Button>
        </HStack>
        <ViewModeToggle />
      </HStack>

      {/* Branch Selection Dialog */}
      <DialogRoot
        open={isDialogOpen}
        onOpenChange={({ open }) => !open && setIsDialogOpen(false)}
        placement="center"
        size={{ base: "xs", md: "xl" }}
      >
        <DialogContent maxW={{ base: "xs", md: "2xl" }}>
          <DialogHeader>
            <DialogTitle>Select Branch</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <VStack gap={4} align="stretch">
              <Text fontSize="sm" color="red.500">
                Select a branch to switch to. You will be redirected to the
                project main page.
              </Text>
              {isLoadingChangeOrders || isLoadingLocks ? (
                <Text>Loading branches...</Text>
              ) : (
                <DataTable
                  data={branchData}
                  columns={branchColumns}
                  tableId="branch-selector-table"
                  isLoading={isLoadingChangeOrders || isLoadingLocks}
                  count={branchData.length}
                  page={1}
                  onPageChange={() => {}}
                  pageSize={branchData.length}
                  onRowClick={(branch: BranchData) => {
                    // Prevent selection of locked branches (except current)
                    if (branch.isLocked && branch.branch !== currentBranch) {
                      showErrorToast(
                        `Cannot switch to branch ${branch.branch} because it is locked.`,
                      )
                      return
                    }
                    handleBranchSelect(branch)
                  }}
                />
              )}
            </VStack>
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray">
                Cancel
              </Button>
            </DialogActionTrigger>
          </DialogFooter>
          <DialogCloseTrigger />
        </DialogContent>
      </DialogRoot>

      {/* Confirmation Dialog */}
      <DialogRoot
        open={isConfirmDialogOpen}
        onOpenChange={({ open }) => !open && setIsConfirmDialogOpen(false)}
        placement="center"
        size={{ base: "xs", md: "md" }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Branch Switch</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <VStack gap={4} align="stretch">
              <Text>
                You are about to switch from branch{" "}
                <strong>{currentBranch}</strong> to branch{" "}
                <strong>{selectedBranch}</strong>.
              </Text>
              <Box
                p={3}
                borderRadius="md"
                bg="orange.50"
                borderWidth="1px"
                borderColor="orange.200"
              >
                <Text fontSize="sm" color="orange.800">
                  <strong>Warning:</strong> You will be redirected to the
                  project main page after switching branches.
                </Text>
              </Box>
            </VStack>
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                onClick={() => {
                  setIsConfirmDialogOpen(false)
                  setSelectedBranch(null)
                }}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="blue"
              onClick={handleConfirmSwitch}
            >
              Confirm Switch
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </DialogContent>
      </DialogRoot>
    </>
  )
}

export default BranchSelector
