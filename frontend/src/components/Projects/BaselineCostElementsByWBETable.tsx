import {
  Box,
  Button,
  Collapsible,
  EmptyState,
  Flex,
  Heading,
  IconButton,
  SkeletonText,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { useState } from "react"
import { FiChevronDown, FiChevronUp } from "react-icons/fi"
import type {
  BaselineCostElementsByWBEPublic,
  BaselineCostElementWithCostElementPublic,
  BaselineWBEPublic,
} from "@/client"
import { BaselineLogsService } from "@/client"
import { DataTable } from "@/components/DataTable/DataTable"
import type { ColumnDefExtended } from "@/components/DataTable/types"
import { useColorModeValue } from "@/components/ui/color-mode"
import { useTimeMachine } from "@/context/TimeMachineContext"
import { getCpiStatus, getSpiStatus } from "@/utils/statusIndicators"

interface BaselineCostElementsByWBETableProps {
  projectId: string
  baselineId: string
}

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

const costElementColumns: ColumnDefExtended<BaselineCostElementWithCostElementPublic>[] =
  [
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
    {
      accessorKey: "department_code",
      header: "Department Code",
      enableSorting: true,
      enableResizing: true,
      enableColumnFilter: true,
      filterType: "text",
      size: 120,
      defaultVisible: true,
    },
    {
      accessorKey: "budget_bac",
      header: "Budget (BAC)",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string),
    },
    {
      accessorKey: "revenue_plan",
      header: "Revenue Plan",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string),
    },
    {
      accessorKey: "planned_value",
      header: "Planned Value",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) =>
        formatCurrency(getValue() as string | null | undefined),
    },
    {
      accessorKey: "actual_ac",
      header: "Actual AC",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
    {
      accessorKey: "forecast_eac",
      header: "Forecast EAC",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
    {
      accessorKey: "earned_ev",
      header: "Earned EV",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatCurrency(getValue() as string | null),
    },
  ]

export default function BaselineCostElementsByWBETable({
  projectId,
  baselineId,
}: BaselineCostElementsByWBETableProps) {
  const { controlDate } = useTimeMachine()
  const queryKey = [
    "baseline-cost-elements-by-wbe",
    projectId,
    baselineId,
    controlDate,
  ]

  const { data, isLoading } = useQuery<BaselineCostElementsByWBEPublic>({
    queryKey,
    queryFn: () =>
      BaselineLogsService.getBaselineCostElementsByWbe({
        projectId: projectId,
        baselineId: baselineId,
      }),
    enabled: !!projectId && !!baselineId,
  })

  if (isLoading) {
    return (
      <Box>
        <SkeletonText noOfLines={10} gap={4} />
      </Box>
    )
  }

  if (!data || !data.wbes || data.wbes.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Title>No cost elements found</EmptyState.Title>
          <EmptyState.Description>
            This baseline has no cost elements
          </EmptyState.Description>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  return (
    <VStack align="stretch" gap={6}>
      {data.wbes.map((wbe) => (
        <WBEAccordionItem
          key={wbe.wbe_id}
          wbe={wbe}
          projectId={projectId}
          baselineId={baselineId}
        />
      ))}
    </VStack>
  )
}

function WBEAccordionItem({
  wbe,
  projectId,
  baselineId,
}: {
  wbe: {
    wbe_id: string
    machine_type: string
    serial_number?: string | null
    cost_elements?: Array<BaselineCostElementWithCostElementPublic> | null
    wbe_total_budget_bac: string
    wbe_total_revenue_plan: string
    wbe_total_planned_value: string
    wbe_total_actual_ac?: string | null
    wbe_total_forecast_eac?: string | null
    wbe_total_earned_ev?: string | null
  }
  projectId: string
  baselineId: string
}) {
  const [isOpen, setIsOpen] = useState(false)
  const { controlDate } = useTimeMachine()
  // Theme-aware colors
  const cardBg = useColorModeValue("bg.surface", "bg.surface")
  const borderCol = useColorModeValue("border", "border")
  const mutedText = useColorModeValue("fg.muted", "fg.muted")
  const subtleBg = useColorModeValue("bg.subtle", "bg.subtle")
  const hoverBg = useColorModeValue("bg.subtle", "bg.subtle")

  // Fetch WBE snapshot for metrics
  const { data: wbeSnapshot } = useQuery<BaselineWBEPublic>({
    queryKey: [
      "baseline-wbe-snapshot",
      projectId,
      baselineId,
      wbe.wbe_id,
      controlDate,
    ],
    queryFn: () =>
      BaselineLogsService.getBaselineWbeSnapshotDetail({
        projectId: projectId,
        baselineId: baselineId,
        wbeId: wbe.wbe_id,
      }),
    enabled: !!projectId && !!baselineId && !!wbe.wbe_id,
  })

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

  const cpiStatus = getCpiStatus(wbeSnapshot?.cpi)
  const spiStatus = getSpiStatus(wbeSnapshot?.spi)
  const CpiIcon = cpiStatus.icon
  const SpiIcon = spiStatus.icon

  return (
    <Box
      borderWidth="1px"
      borderRadius="md"
      borderColor={borderCol}
      bg={cardBg}
    >
      <Collapsible.Root open={isOpen} onOpenChange={(e) => setIsOpen(e.open)}>
        <Collapsible.Trigger asChild>
          <Button
            variant="ghost"
            width="100%"
            justifyContent="space-between"
            p={6}
            _hover={{ bg: hoverBg }}
            _active={{ bg: hoverBg }}
          >
            <Flex
              justifyContent="space-between"
              alignItems="flex-start"
              width="100%"
              gap={6}
            >
              <VStack align="start" gap={2} flex={1} minWidth={0}>
                <Link
                  to="/projects/$id/baselines/$baselineId/wbes/$wbeId"
                  params={{
                    id: projectId,
                    baselineId: baselineId,
                    wbeId: wbe.wbe_id,
                  }}
                  search={{ tab: "metrics", baselineTab: "by-wbe", page: 1 }}
                >
                  <Text
                    fontWeight="bold"
                    color="blue.500"
                    _hover={{ textDecoration: "underline" }}
                  >
                    {wbe.machine_type}
                  </Text>
                </Link>
                {wbe.serial_number && (
                  <Text fontSize="sm" color={mutedText}>
                    {wbe.serial_number}
                  </Text>
                )}
              </VStack>
              <VStack align="end" gap={2} flexShrink={0}>
                <Text fontSize="sm" color={mutedText}>
                  {wbe.cost_elements?.length || 0} cost elements
                </Text>
                <Flex
                  alignItems="center"
                  gap={4}
                  flexWrap="wrap"
                  justifyContent="flex-end"
                >
                  <Text fontSize="sm" fontWeight="medium">
                    Total BAC: {formatCurrency(wbe.wbe_total_budget_bac)}
                  </Text>
                  {wbeSnapshot && (
                    <>
                      <Flex alignItems="center" gap={1}>
                        <CpiIcon color={cpiStatus.color} size={14} />
                        <Text fontSize="xs" color={cpiStatus.color}>
                          CPI: {formatIndex(wbeSnapshot.cpi)}
                        </Text>
                      </Flex>
                      <Flex alignItems="center" gap={1}>
                        <SpiIcon color={spiStatus.color} size={14} />
                        <Text fontSize="xs" color={spiStatus.color}>
                          SPI: {formatIndex(wbeSnapshot.spi)}
                        </Text>
                      </Flex>
                    </>
                  )}
                </Flex>
              </VStack>
              <IconButton
                aria-label={isOpen ? "Collapse" : "Expand"}
                variant="ghost"
                size="sm"
                flexShrink={0}
              >
                {isOpen ? <FiChevronUp /> : <FiChevronDown />}
              </IconButton>
            </Flex>
          </Button>
        </Collapsible.Trigger>
        <Collapsible.Content>
          <Box p={6} pt={4}>
            {/* WBE Totals Summary */}
            <Box
              p={6}
              mb={6}
              borderWidth="1px"
              borderRadius="md"
              borderColor={borderCol}
              bg={subtleBg}
            >
              <Heading size="sm" mb={4}>
                WBE Totals
              </Heading>
              <Flex gap={6} wrap="wrap">
                <Box minWidth="150px">
                  <Text fontSize="xs" color={mutedText} mb={1}>
                    Total Budget BAC
                  </Text>
                  <Text fontWeight="bold">
                    {formatCurrency(wbe.wbe_total_budget_bac)}
                  </Text>
                </Box>
                <Box minWidth="150px">
                  <Text fontSize="xs" color={mutedText} mb={1}>
                    Total Planned Value
                  </Text>
                  <Text fontWeight="bold">
                    {formatCurrency(wbe.wbe_total_planned_value)}
                  </Text>
                </Box>
                <Box minWidth="150px">
                  <Text fontSize="xs" color={mutedText} mb={1}>
                    Total Revenue Plan
                  </Text>
                  <Text fontWeight="bold">
                    {formatCurrency(wbe.wbe_total_revenue_plan)}
                  </Text>
                </Box>
                {wbe.wbe_total_actual_ac && (
                  <Box minWidth="150px">
                    <Text fontSize="xs" color={mutedText} mb={1}>
                      Total Actual AC
                    </Text>
                    <Text fontWeight="bold">
                      {formatCurrency(wbe.wbe_total_actual_ac)}
                    </Text>
                  </Box>
                )}
                {wbe.wbe_total_forecast_eac && (
                  <Box minWidth="150px">
                    <Text fontSize="xs" color={mutedText} mb={1}>
                      Total Forecast EAC
                    </Text>
                    <Text fontWeight="bold">
                      {formatCurrency(wbe.wbe_total_forecast_eac)}
                    </Text>
                  </Box>
                )}
                {wbe.wbe_total_earned_ev && (
                  <Box minWidth="150px">
                    <Text fontSize="xs" color={mutedText} mb={1}>
                      Total Earned EV
                    </Text>
                    <Text fontWeight="bold">
                      {formatCurrency(wbe.wbe_total_earned_ev)}
                    </Text>
                  </Box>
                )}
              </Flex>
            </Box>

            {/* Cost Elements Table */}
            {wbe.cost_elements && wbe.cost_elements.length > 0 ? (
              <DataTable
                data={wbe.cost_elements}
                columns={costElementColumns}
                tableId={`baseline-cost-elements-wbe-${wbe.wbe_id}`}
                isLoading={false}
                count={wbe.cost_elements.length}
                page={1}
                onPageChange={() => {}}
                pageSize={wbe.cost_elements.length}
              />
            ) : (
              <EmptyState.Root>
                <EmptyState.Content>
                  <EmptyState.Title>
                    No cost elements for this WBE
                  </EmptyState.Title>
                </EmptyState.Content>
              </EmptyState.Root>
            )}
          </Box>
        </Collapsible.Content>
      </Collapsible.Root>
    </Box>
  )
}
