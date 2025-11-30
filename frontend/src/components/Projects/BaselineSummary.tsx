import {
  Box,
  Grid,
  Heading,
  SkeletonText,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import type { BaselineProjectPublic, BaselineSummaryPublic } from "@/client"
import { BaselineLogsService } from "@/client"
import { useColorModeValue } from "@/components/ui/color-mode"
import { useTimeMachine } from "@/context/TimeMachineContext"
import {
  getCpiStatus,
  getCvStatus,
  getSpiStatus,
  getSvStatus,
  getTcpiStatus,
} from "@/utils/statusIndicators"

interface BaselineSummaryProps {
  projectId: string
  baselineId: string
}

export default function BaselineSummary({
  projectId,
  baselineId,
}: BaselineSummaryProps) {
  const { controlDate } = useTimeMachine()
  // Theme-aware colors (declare before early returns)
  const cardBg = useColorModeValue("bg.surface", "bg.surface")
  const borderCol = useColorModeValue("border", "border")
  const mutedText = useColorModeValue("fg.muted", "fg.muted")

  const queryKey = [
    "baseline-snapshot-summary",
    projectId,
    baselineId,
    controlDate,
  ]

  const { data: summary, isLoading: isLoadingSummary } =
    useQuery<BaselineSummaryPublic>({
      queryKey,
      queryFn: () =>
        BaselineLogsService.getBaselineSnapshotSummary({
          projectId: projectId,
          baselineId: baselineId,
        }),
      enabled: !!projectId && !!baselineId,
    })

  // Fetch project snapshot for EVM indices
  const projectSnapshotQueryKey = [
    "baseline-project-snapshot",
    projectId,
    baselineId,
    controlDate,
  ]

  const { data: projectSnapshot, isLoading: isLoadingSnapshot } =
    useQuery<BaselineProjectPublic>({
      queryKey: projectSnapshotQueryKey,
      queryFn: () =>
        BaselineLogsService.getBaselineProjectSnapshot({
          projectId: projectId,
          baselineId: baselineId,
        }),
      enabled: !!projectId && !!baselineId,
    })

  const isLoading = isLoadingSummary || isLoadingSnapshot

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

  if (isLoading) {
    return (
      <Box mb={6}>
        <Heading size="md" mb={4}>
          Baseline Summary
        </Heading>
        <Grid
          templateColumns={{
            base: "1fr",
            md: "repeat(2, 1fr)",
            lg: "repeat(3, 1fr)",
          }}
          gap={4}
        >
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((i) => (
            <Box
              key={i}
              p={4}
              borderWidth="1px"
              borderRadius="md"
              borderColor={borderCol}
              bg={cardBg}
            >
              <SkeletonText noOfLines={2} />
            </Box>
          ))}
        </Grid>
      </Box>
    )
  }

  if (!summary) {
    return null
  }

  const totalBudgetBac = Number(summary.total_budget_bac)
  const totalRevenuePlan = Number(summary.total_revenue_plan)
  const totalPlannedValue = Number(summary.total_planned_value)
  const totalActualAc = summary.total_actual_ac
    ? Number(summary.total_actual_ac)
    : null
  const totalForecastEac = summary.total_forecast_eac
    ? Number(summary.total_forecast_eac)
    : null
  const totalEarnedEv = summary.total_earned_ev
    ? Number(summary.total_earned_ev)
    : null
  const costElementCount = summary.cost_element_count

  // Get EVM indices from project snapshot
  const cpi = projectSnapshot?.cpi
  const spi = projectSnapshot?.spi
  const tcpi = projectSnapshot?.tcpi
  const costVariance = projectSnapshot?.cost_variance
  const scheduleVariance = projectSnapshot?.schedule_variance

  const cpiStatus = getCpiStatus(cpi)
  const spiStatus = getSpiStatus(spi)
  const tcpiStatus = getTcpiStatus(tcpi)
  const cvStatus = getCvStatus(costVariance)
  const svStatus = getSvStatus(scheduleVariance)

  const CpiIcon = cpiStatus.icon
  const SpiIcon = spiStatus.icon
  const TcpiIcon = tcpiStatus.icon
  const CvIcon = cvStatus.icon
  const SvIcon = svStatus.icon

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

  const formatTcpi = (tcpi: string | null | undefined): string => {
    if (tcpi === null || tcpi === undefined) {
      return "N/A"
    }
    if (tcpi === "overrun") {
      return "overrun"
    }
    return formatIndex(tcpi)
  }

  return (
    <Box mb={6}>
      <Heading size="md" mb={4}>
        Baseline Snapshot Summary
      </Heading>
      <Grid
        templateColumns={{
          base: "1fr",
          md: "repeat(2, 1fr)",
          lg: "repeat(3, 1fr)",
        }}
        gap={4}
      >
        {/* Card 1: Total Budget BAC */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Total Budget BAC
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(totalBudgetBac)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Budget at Completion
            </Text>
          </VStack>
        </Box>

        {/* Card 2: Total Revenue Plan */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Total Revenue Plan
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(totalRevenuePlan)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Planned Revenue
            </Text>
          </VStack>
        </Box>

        {/* Card 3: Total Planned Value */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Total Planned Value
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(totalPlannedValue)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Planned Value
            </Text>
          </VStack>
        </Box>

        {/* Card 4: Total Actual AC */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Total Actual AC
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(totalActualAc)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Actual Cost
            </Text>
          </VStack>
        </Box>

        {/* Card 5: Total Forecast EAC */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Total Forecast EAC
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(totalForecastEac)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Estimate at Completion
            </Text>
          </VStack>
        </Box>

        {/* Card 6: Total Earned EV */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Total Earned EV
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(totalEarnedEv)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Earned Value
            </Text>
          </VStack>
        </Box>

        {/* Card 7: Cost Element Count */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Cost Elements
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {costElementCount}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Total cost elements in baseline
            </Text>
          </VStack>
        </Box>

        {/* Card 8: Cost Performance Index (CPI) */}
        {projectSnapshot && (
          <Box
            p={4}
            borderWidth="1px"
            borderRadius="md"
            borderColor={borderCol}
            bg={cardBg}
          >
            <VStack align="stretch" gap={1}>
              <Text fontSize="sm" color={mutedText} fontWeight="medium">
                Cost Performance Index (CPI)
              </Text>
              <Text fontSize="xl" fontWeight="bold" color={cpiStatus.color}>
                {formatIndex(cpi)}
              </Text>
              <Text fontSize="xs" color={cpiStatus.color} mt={1}>
                <CpiIcon style={{ display: "inline", marginRight: "4px" }} />
                {cpiStatus.label}
              </Text>
            </VStack>
          </Box>
        )}

        {/* Card 9: Schedule Performance Index (SPI) */}
        {projectSnapshot && (
          <Box
            p={4}
            borderWidth="1px"
            borderRadius="md"
            borderColor={borderCol}
            bg={cardBg}
          >
            <VStack align="stretch" gap={1}>
              <Text fontSize="sm" color={mutedText} fontWeight="medium">
                Schedule Performance Index (SPI)
              </Text>
              <Text fontSize="xl" fontWeight="bold" color={spiStatus.color}>
                {formatIndex(spi)}
              </Text>
              <Text fontSize="xs" color={spiStatus.color} mt={1}>
                <SpiIcon style={{ display: "inline", marginRight: "4px" }} />
                {spiStatus.label}
              </Text>
            </VStack>
          </Box>
        )}

        {/* Card 10: To-Complete Performance Index (TCPI) */}
        {projectSnapshot && (
          <Box
            p={4}
            borderWidth="1px"
            borderRadius="md"
            borderColor={borderCol}
            bg={cardBg}
          >
            <VStack align="stretch" gap={1}>
              <Text fontSize="sm" color={mutedText} fontWeight="medium">
                To-Complete Performance Index (TCPI)
              </Text>
              <Text fontSize="xl" fontWeight="bold" color={tcpiStatus.color}>
                {formatTcpi(tcpi)}
              </Text>
              <Text fontSize="xs" color={tcpiStatus.color} mt={1}>
                <TcpiIcon style={{ display: "inline", marginRight: "4px" }} />
                {tcpiStatus.label}
              </Text>
            </VStack>
          </Box>
        )}

        {/* Card 11: Cost Variance (CV) */}
        {projectSnapshot && (
          <Box
            p={4}
            borderWidth="1px"
            borderRadius="md"
            borderColor={borderCol}
            bg={cardBg}
          >
            <VStack align="stretch" gap={1}>
              <Text fontSize="sm" color={mutedText} fontWeight="medium">
                Cost Variance (CV)
              </Text>
              <Text fontSize="xl" fontWeight="bold" color={cvStatus.color}>
                {formatCurrency(costVariance)}
              </Text>
              <Text fontSize="xs" color={cvStatus.color} mt={1}>
                <CvIcon style={{ display: "inline", marginRight: "4px" }} />
                {cvStatus.label}
              </Text>
            </VStack>
          </Box>
        )}

        {/* Card 12: Schedule Variance (SV) */}
        {projectSnapshot && (
          <Box
            p={4}
            borderWidth="1px"
            borderRadius="md"
            borderColor={borderCol}
            bg={cardBg}
          >
            <VStack align="stretch" gap={1}>
              <Text fontSize="sm" color={mutedText} fontWeight="medium">
                Schedule Variance (SV)
              </Text>
              <Text fontSize="xl" fontWeight="bold" color={svStatus.color}>
                {formatCurrency(scheduleVariance)}
              </Text>
              <Text fontSize="xs" color={svStatus.color} mt={1}>
                <SvIcon style={{ display: "inline", marginRight: "4px" }} />
                {svStatus.label}
              </Text>
            </VStack>
          </Box>
        )}
      </Grid>
    </Box>
  )
}
