import { Box, Flex, Heading, SkeletonText, Stack, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import {
  FiAlertCircle,
  FiMinus,
  FiTrendingDown,
  FiTrendingUp,
} from "react-icons/fi"
import {
  type CostPerformanceReportPublic,
  type CostPerformanceReportRowPublic,
  ReportsService,
} from "@/client"
import { DataTable } from "@/components/DataTable/DataTable"
import type { ColumnDefExtended } from "@/components/DataTable/types"
import { useColorModeValue } from "@/components/ui/color-mode"
import { useTimeMachine } from "@/context/TimeMachineContext"

// Formatting helpers
const formatCurrency = (value: string | number | null | undefined): string => {
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
  if (value === "overrun") {
    return "overrun"
  }
  const numValue = typeof value === "string" ? Number(value) : value
  if (Number.isNaN(numValue)) {
    return "N/A"
  }
  return numValue.toFixed(2)
}

const formatPercent = (value: string | number | null | undefined): string => {
  if (value === null || value === undefined) {
    return "N/A"
  }
  const numValue = typeof value === "string" ? Number(value) : value
  if (Number.isNaN(numValue)) {
    return "N/A"
  }
  return `${(numValue * 100).toFixed(2)}%`
}

const formatTcpi = (value: string | number | null | undefined): string => {
  if (value === null || value === undefined) {
    return "N/A"
  }
  if (value === "overrun") {
    return "overrun"
  }
  const numValue = typeof value === "string" ? Number(value) : value
  if (Number.isNaN(numValue)) {
    return "N/A"
  }
  return numValue.toFixed(2)
}

// Status indicator helpers
type StatusIndicator = {
  color: string
  icon: typeof FiTrendingUp
  label: string
}

const getCpiStatus = (cpi: string | null | undefined): StatusIndicator => {
  if (cpi === null || cpi === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  const numValue = Number(cpi)
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue < 0.95) {
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Over Budget",
    }
  }
  if (numValue < 1.0) {
    return {
      color: "yellow.500",
      icon: FiMinus,
      label: "On Target",
    }
  }
  return {
    color: "green.500",
    icon: FiTrendingUp,
    label: "Under Budget",
  }
}

const getSpiStatus = (spi: string | null | undefined): StatusIndicator => {
  if (spi === null || spi === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  const numValue = Number(spi)
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue < 0.95) {
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Behind Schedule",
    }
  }
  if (numValue < 1.0) {
    return {
      color: "yellow.500",
      icon: FiMinus,
      label: "On Schedule",
    }
  }
  return {
    color: "green.500",
    icon: FiTrendingUp,
    label: "Ahead of Schedule",
  }
}

const getTcpiStatus = (
  tcpi: string | number | null | undefined,
): StatusIndicator => {
  if (tcpi === null || tcpi === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (tcpi === "overrun") {
    return {
      color: "red.500",
      icon: FiAlertCircle,
      label: "Overrun",
    }
  }
  const numValue = typeof tcpi === "string" ? Number(tcpi) : tcpi
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue > 1.2) {
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Difficult",
    }
  }
  if (numValue > 1.0) {
    return {
      color: "yellow.500",
      icon: FiMinus,
      label: "Challenging",
    }
  }
  return {
    color: "green.500",
    icon: FiTrendingUp,
    label: "Achievable",
  }
}

const getVarianceStatus = (
  value: string | number | null | undefined,
): StatusIndicator => {
  if (value === null || value === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  const numValue = typeof value === "string" ? Number(value) : value
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue < 0) {
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Negative",
    }
  }
  if (numValue === 0) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "Zero",
    }
  }
  return {
    color: "green.500",
    icon: FiTrendingUp,
    label: "Positive",
  }
}

// Column definitions for cost performance report
const reportColumns: ColumnDefExtended<CostPerformanceReportRowPublic>[] = [
  // Hierarchy columns
  {
    accessorKey: "wbe_name",
    header: "WBE",
    enableSorting: true,
    enableResizing: true,
    enableColumnFilter: true,
    filterType: "text",
    size: 150,
    defaultVisible: true,
  },
  {
    accessorKey: "wbe_serial_number",
    header: "Serial Number",
    enableSorting: true,
    enableResizing: true,
    size: 120,
    defaultVisible: true,
    cell: ({ getValue }) => (getValue() as string | null) || "N/A",
  },
  {
    accessorKey: "department_code",
    header: "Dept Code",
    enableSorting: true,
    enableResizing: true,
    enableColumnFilter: true,
    filterType: "text",
    size: 100,
    defaultVisible: true,
  },
  {
    accessorKey: "department_name",
    header: "Department",
    enableSorting: true,
    enableResizing: true,
    enableColumnFilter: true,
    filterType: "text",
    size: 150,
    defaultVisible: true,
  },
  // Core metric columns
  {
    accessorKey: "budget_bac",
    header: "BAC",
    enableSorting: true,
    enableResizing: true,
    size: 120,
    defaultVisible: true,
    cell: ({ getValue }) =>
      formatCurrency(getValue() as string | number | null | undefined),
  },
  {
    accessorKey: "planned_value",
    header: "PV",
    enableSorting: true,
    enableResizing: true,
    size: 120,
    defaultVisible: true,
    cell: ({ getValue }) =>
      formatCurrency(getValue() as string | number | null | undefined),
  },
  {
    accessorKey: "earned_value",
    header: "EV",
    enableSorting: true,
    enableResizing: true,
    size: 120,
    defaultVisible: true,
    cell: ({ getValue }) =>
      formatCurrency(getValue() as string | number | null | undefined),
  },
  {
    accessorKey: "actual_cost",
    header: "AC",
    enableSorting: true,
    enableResizing: true,
    size: 120,
    defaultVisible: true,
    cell: ({ getValue }) =>
      formatCurrency(getValue() as string | number | null | undefined),
  },
  // Performance index columns with status indicators
  {
    accessorKey: "cpi",
    header: "CPI",
    enableSorting: true,
    enableResizing: true,
    size: 120,
    defaultVisible: true,
    cell: ({ getValue }) => {
      const value = getValue() as string | number | null | undefined
      const status = getCpiStatus(
        typeof value === "number" ? String(value) : value,
      )
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
    size: 120,
    defaultVisible: true,
    cell: ({ getValue }) => {
      const value = getValue() as string | number | null | undefined
      const status = getSpiStatus(
        typeof value === "number" ? String(value) : value,
      )
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
    accessorKey: "tcpi",
    header: "TCPI",
    enableSorting: true,
    enableResizing: true,
    size: 120,
    defaultVisible: true,
    cell: ({ getValue }) => {
      const value = getValue() as string | number | null | undefined
      const status = getTcpiStatus(value)
      const StatusIcon = status.icon
      return (
        <Flex alignItems="center" gap={2}>
          <StatusIcon color={status.color} />
          <Text color={status.color} fontWeight="medium">
            {formatTcpi(value)}
          </Text>
        </Flex>
      )
    },
  },
  // Variance columns with status indicators
  {
    accessorKey: "cost_variance",
    header: "CV",
    enableSorting: true,
    enableResizing: true,
    size: 140,
    defaultVisible: true,
    cell: ({ getValue }) => {
      const value = getValue() as string | number | null | undefined
      const status = getVarianceStatus(value)
      const StatusIcon = status.icon
      return (
        <Flex alignItems="center" gap={2}>
          <StatusIcon color={status.color} />
          <Text color={status.color} fontWeight="medium">
            {formatCurrency(value)}
          </Text>
        </Flex>
      )
    },
  },
  {
    accessorKey: "schedule_variance",
    header: "SV",
    enableSorting: true,
    enableResizing: true,
    size: 140,
    defaultVisible: true,
    cell: ({ getValue }) => {
      const value = getValue() as string | number | null | undefined
      const status = getVarianceStatus(value)
      const StatusIcon = status.icon
      return (
        <Flex alignItems="center" gap={2}>
          <StatusIcon color={status.color} />
          <Text color={status.color} fontWeight="medium">
            {formatCurrency(value)}
          </Text>
        </Flex>
      )
    },
  },
  // Percent complete columns (optional)
  {
    id: "ev_percent",
    header: "EV/BAC %",
    enableSorting: true,
    enableResizing: true,
    size: 100,
    defaultVisible: false,
    accessorFn: (row) => {
      const ev = row.earned_value ? Number(row.earned_value) : 0
      const bac = row.budget_bac ? Number(row.budget_bac) : 0
      if (bac === 0) return null
      return ev / bac
    },
    cell: ({ getValue }) =>
      formatPercent(getValue() as string | number | null | undefined),
  },
  {
    id: "pv_percent",
    header: "PV/BAC %",
    enableSorting: true,
    enableResizing: true,
    size: 100,
    defaultVisible: false,
    accessorFn: (row) => {
      const pv = row.planned_value ? Number(row.planned_value) : 0
      const bac = row.budget_bac ? Number(row.budget_bac) : 0
      if (bac === 0) return null
      return pv / bac
    },
    cell: ({ getValue }) =>
      formatPercent(getValue() as string | number | null | undefined),
  },
]

interface CostPerformanceReportProps {
  projectId: string
}

export default function CostPerformanceReport({
  projectId,
}: CostPerformanceReportProps) {
  const { controlDate } = useTimeMachine()
  const mutedText = useColorModeValue("fg.muted", "fg.muted")
  const [page, setPage] = useState(1)
  const pageSize = 25
  const navigate = useNavigate()

  const queryKey = ["cost-performance-report", projectId, controlDate]

  const {
    data: report,
    isLoading,
    error,
  } = useQuery<CostPerformanceReportPublic>({
    queryKey,
    queryFn: () =>
      ReportsService.getProjectCostPerformanceReportEndpoint({
        projectId: projectId,
      }),
    enabled: !!projectId,
  })

  // Loading state
  if (isLoading) {
    return (
      <Box>
        <Stack gap={4}>
          <SkeletonText noOfLines={1} width="200px" />
          <SkeletonText noOfLines={5} width="100%" />
        </Stack>
      </Box>
    )
  }

  // Error state
  if (error) {
    return (
      <Box>
        <Stack gap={4}>
          <Box display="flex" alignItems="center" gap={2} color="fg.error">
            <FiAlertCircle />
            <Text>Error loading cost performance report</Text>
          </Box>
          <Text fontSize="sm" color={mutedText}>
            {error instanceof Error ? error.message : "Unknown error"}
          </Text>
        </Stack>
      </Box>
    )
  }

  // Empty state
  if (!report || !report.rows || report.rows.length === 0) {
    return (
      <Box>
        <Stack gap={4}>
          <Heading size="md">Cost Performance Report</Heading>
          <Text color={mutedText}>
            No cost elements found for this project.
          </Text>
        </Stack>
      </Box>
    )
  }

  // Report data available
  const summary = report.summary

  return (
    <Box>
      <Stack gap={4}>
        <Heading size="md">Cost Performance Report</Heading>
        <Text fontSize="sm" color={mutedText}>
          Control Date: {new Date(report.control_date).toLocaleDateString()}
        </Text>
        <DataTable
          data={report.rows || []}
          columns={reportColumns}
          tableId="cost-performance-report"
          count={report.rows?.length || 0}
          page={page}
          onPageChange={setPage}
          pageSize={pageSize}
          isLoading={false}
          onRowClick={(row) => {
            // Navigate to cost element detail
            const costElementId = row.cost_element_id
            const wbeId = row.wbe_id
            navigate({
              to: "/projects/$id/wbes/$wbeId/cost-elements/$costElementId",
              params: {
                id: projectId,
                wbeId: wbeId,
                costElementId: costElementId,
              },
              search: (prev) => ({
                ...prev,
                page: prev.page ?? 1,
                tab: (prev.tab ?? "info") as
                  | "summary"
                  | "info"
                  | "cost-summary"
                  | "metrics"
                  | "timeline",
                view: "info" as const,
              }),
            })
          }}
        />
        {/* Summary Row */}
        <Box
          borderWidth="2px"
          borderRadius="md"
          p={4}
          bg="bg.subtle"
          borderColor="border"
        >
          <Heading size="sm" mb={3}>
            Project Summary
          </Heading>
          <Box
            display="grid"
            gridTemplateColumns={{
              base: "1fr",
              md: "repeat(2, 1fr)",
              lg: "repeat(4, 1fr)",
            }}
            gap={4}
          >
            <Box>
              <Text fontSize="xs" color={mutedText} mb={1}>
                Budget at Completion (BAC)
              </Text>
              <Text fontSize="lg" fontWeight="bold">
                {formatCurrency(summary.budget_bac)}
              </Text>
            </Box>
            <Box>
              <Text fontSize="xs" color={mutedText} mb={1}>
                Planned Value (PV)
              </Text>
              <Text fontSize="lg" fontWeight="bold">
                {formatCurrency(summary.planned_value)}
              </Text>
            </Box>
            <Box>
              <Text fontSize="xs" color={mutedText} mb={1}>
                Earned Value (EV)
              </Text>
              <Text fontSize="lg" fontWeight="bold">
                {formatCurrency(summary.earned_value)}
              </Text>
            </Box>
            <Box>
              <Text fontSize="xs" color={mutedText} mb={1}>
                Actual Cost (AC)
              </Text>
              <Text fontSize="lg" fontWeight="bold">
                {formatCurrency(summary.actual_cost)}
              </Text>
            </Box>
            <Box>
              <Text fontSize="xs" color={mutedText} mb={1}>
                Cost Performance Index (CPI)
              </Text>
              <Flex alignItems="center" gap={2}>
                {summary.cpi && (
                  <>
                    {(() => {
                      const status = getCpiStatus(summary.cpi)
                      const StatusIcon = status.icon
                      return <StatusIcon color={status.color} />
                    })()}
                    <Text
                      fontSize="lg"
                      fontWeight="bold"
                      color={getCpiStatus(summary.cpi).color}
                    >
                      {formatIndex(summary.cpi)}
                    </Text>
                  </>
                )}
                {!summary.cpi && (
                  <Text fontSize="lg" fontWeight="bold" color="gray.500">
                    N/A
                  </Text>
                )}
              </Flex>
            </Box>
            <Box>
              <Text fontSize="xs" color={mutedText} mb={1}>
                Schedule Performance Index (SPI)
              </Text>
              <Flex alignItems="center" gap={2}>
                {summary.spi && (
                  <>
                    {(() => {
                      const status = getSpiStatus(summary.spi)
                      const StatusIcon = status.icon
                      return <StatusIcon color={status.color} />
                    })()}
                    <Text
                      fontSize="lg"
                      fontWeight="bold"
                      color={getSpiStatus(summary.spi).color}
                    >
                      {formatIndex(summary.spi)}
                    </Text>
                  </>
                )}
                {!summary.spi && (
                  <Text fontSize="lg" fontWeight="bold" color="gray.500">
                    N/A
                  </Text>
                )}
              </Flex>
            </Box>
            <Box>
              <Text fontSize="xs" color={mutedText} mb={1}>
                Cost Variance (CV)
              </Text>
              <Flex alignItems="center" gap={2}>
                {(() => {
                  const status = getVarianceStatus(summary.cost_variance)
                  const StatusIcon = status.icon
                  return (
                    <>
                      <StatusIcon color={status.color} />
                      <Text
                        fontSize="lg"
                        fontWeight="bold"
                        color={status.color}
                      >
                        {formatCurrency(summary.cost_variance)}
                      </Text>
                    </>
                  )
                })()}
              </Flex>
            </Box>
            <Box>
              <Text fontSize="xs" color={mutedText} mb={1}>
                Schedule Variance (SV)
              </Text>
              <Flex alignItems="center" gap={2}>
                {(() => {
                  const status = getVarianceStatus(summary.schedule_variance)
                  const StatusIcon = status.icon
                  return (
                    <>
                      <StatusIcon color={status.color} />
                      <Text
                        fontSize="lg"
                        fontWeight="bold"
                        color={status.color}
                      >
                        {formatCurrency(summary.schedule_variance)}
                      </Text>
                    </>
                  )
                })()}
              </Flex>
            </Box>
          </Box>
        </Box>
      </Stack>
    </Box>
  )
}
