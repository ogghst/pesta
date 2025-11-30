/**
 * BaselineWBESnapshotsTable Component
 *
 * Displays a table of all WBE snapshots for a baseline with key metrics
 * and links to WBE baseline detail pages.
 */

import { Box, EmptyState, Flex, Heading, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import type { BaselineWBEPublic } from "@/client"
import { BaselineLogsService } from "@/client"

// Extended type with WBE details (will be available after client regeneration)
type BaselineWBEPublicWithWBE = BaselineWBEPublic & {
  wbe_machine_type?: string | null
  wbe_serial_number?: string | null
}

import { DataTable } from "@/components/DataTable/DataTable"
import type { ColumnDefExtended } from "@/components/DataTable/types"
import { SkeletonText } from "@/components/ui/skeleton"
import { useTimeMachine } from "@/context/TimeMachineContext"
import { getCpiStatus, getSpiStatus } from "@/utils/statusIndicators"

interface BaselineWBESnapshotsTableProps {
  projectId: string
  baselineId: string
}

export default function BaselineWBESnapshotsTable({
  projectId,
  baselineId,
}: BaselineWBESnapshotsTableProps) {
  const { controlDate } = useTimeMachine()

  const queryKey = [
    "baseline-wbe-snapshots",
    projectId,
    baselineId,
    controlDate,
  ]

  const { data: snapshots, isLoading } = useQuery<BaselineWBEPublicWithWBE[]>({
    queryKey,
    queryFn: () =>
      BaselineLogsService.getBaselineWbeSnapshots({
        projectId: projectId,
        baselineId: baselineId,
      }),
    enabled: !!projectId && !!baselineId,
  })

  const formatCurrency = (
    value: string | number | null | undefined,
  ): string => {
    if (value === null || value === undefined) {
      return "N/A"
    }
    const numValue = typeof value === "string" ? Number(value) : value
    if (Number.isNaN(numValue)) {
      return "N/A"
    }
    return `€${numValue.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  const formatIndex = (value: string | number | null | undefined): string => {
    if (value === null || value === undefined) {
      return "N/A"
    }
    const numValue = typeof value === "string" ? Number(value) : value
    if (Number.isNaN(numValue)) {
      return "N/A"
    }
    return numValue.toFixed(2)
  }

  if (isLoading) {
    return (
      <Box>
        <SkeletonText noOfLines={10} gap={4} />
      </Box>
    )
  }

  if (!snapshots || snapshots.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Title>No WBE snapshots found</EmptyState.Title>
          <EmptyState.Description>
            This baseline has no WBE snapshots
          </EmptyState.Description>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  const columns: ColumnDefExtended<BaselineWBEPublicWithWBE>[] = [
    {
      accessorKey: "wbe_machine_type",
      header: "WBE",
      enableSorting: true,
      enableResizing: true,
      size: 200,
      defaultVisible: true,
      cell: ({ row }) => {
        const snapshot = row.original
        return (
          <Box>
            <Link
              to="/projects/$id/baselines/$baselineId/wbes/$wbeId"
              params={{
                id: projectId,
                baselineId: baselineId,
                wbeId: snapshot.wbe_id,
              }}
              search={{ tab: "metrics", baselineTab: "by-wbe", page: 1 }}
            >
              {snapshot.wbe_serial_number && (
                <Text
                  color="blue.500"
                  _hover={{ textDecoration: "underline" }}
                  fontWeight="medium"
                >
                  {snapshot.wbe_machine_type
                    ? snapshot.wbe_machine_type.length > 30
                      ? `${snapshot.wbe_machine_type.slice(0, 30)}...`
                      : snapshot.wbe_machine_type
                    : snapshot.wbe_id.slice(0, 8)}
                </Text>
              )}
            </Link>
            <Text fontSize="xs" color="fg.muted">
              {snapshot.wbe_serial_number}
            </Text>
          </Box>
        )
      },
    },
    {
      accessorKey: "budget_bac",
      header: "Budget BAC",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
    {
      accessorKey: "earned_value",
      header: "Earned EV",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
    {
      accessorKey: "actual_cost",
      header: "Actual AC",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
    {
      accessorKey: "eac",
      header: "Forecast EAC",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
    {
      accessorKey: "cpi",
      header: "CPI",
      enableSorting: true,
      enableResizing: true,
      size: 100,
      defaultVisible: true,
      cell: ({ getValue }) => {
        const value = getValue() as string | null | undefined
        const status = getCpiStatus(value)
        const StatusIcon = status.icon
        return (
          <Flex alignItems="center" gap={2}>
            <StatusIcon color={status.color} />
            <Text color={status.color} fontWeight="medium">
              {formatIndex(value)}
            </Text>
          </Flex>
        )
      },
    },
    {
      accessorKey: "spi",
      header: "SPI",
      enableSorting: true,
      enableResizing: true,
      size: 100,
      defaultVisible: true,
      cell: ({ getValue }) => {
        const value = getValue() as string | null | undefined
        const status = getSpiStatus(value)
        const StatusIcon = status.icon
        return (
          <Flex alignItems="center" gap={2}>
            <StatusIcon color={status.color} />
            <Text color={status.color} fontWeight="medium">
              {formatIndex(value)}
            </Text>
          </Flex>
        )
      },
    },
    {
      accessorKey: "cost_variance",
      header: "Cost Variance",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
    {
      accessorKey: "schedule_variance",
      header: "Schedule Variance",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
  ]

  return (
    <Box>
      <Flex alignItems="center" justifyContent="space-between" mb={4}>
        <Heading size="md">WBE Snapshots</Heading>
      </Flex>
      <DataTable
        data={snapshots}
        columns={columns}
        tableId="baseline-wbe-snapshots-table"
        isLoading={isLoading}
        count={snapshots.length}
        page={1}
        onPageChange={() => {}}
        pageSize={snapshots.length || 10}
      />
    </Box>
  )
}
