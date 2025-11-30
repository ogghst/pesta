/**
 * BaselineProjectSnapshot Component
 *
 * Displays project-level baseline snapshot metrics including all EVM metrics
 * with status indicators for performance indices.
 */

import {
  Box,
  Grid,
  Heading,
  SkeletonText,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import type { BaselineProjectPublic } from "@/client"
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

interface BaselineProjectSnapshotProps {
  projectId: string
  baselineId: string
}

export default function BaselineProjectSnapshot({
  projectId,
  baselineId,
}: BaselineProjectSnapshotProps) {
  const { controlDate } = useTimeMachine()
  // Theme-aware colors (declare before early returns)
  const cardBg = useColorModeValue("bg.surface", "bg.surface")
  const borderCol = useColorModeValue("border", "border")
  const mutedText = useColorModeValue("fg.muted", "fg.muted")

  const queryKey = [
    "baseline-project-snapshot",
    projectId,
    baselineId,
    controlDate,
  ]

  const {
    data: snapshot,
    isLoading,
    isError,
  } = useQuery<BaselineProjectPublic>({
    queryKey,
    queryFn: () =>
      BaselineLogsService.getBaselineProjectSnapshot({
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

  const _formatPercent = (
    value: string | number | null | undefined,
  ): string => {
    if (value === null || value === undefined) {
      return "N/A"
    }
    const numValue = typeof value === "string" ? Number(value) : value
    if (Number.isNaN(numValue)) {
      return "N/A"
    }
    return `${(numValue * 100).toFixed(2)}%`
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

  const formatTcpi = (tcpi: string | null | undefined): string => {
    if (tcpi === null || tcpi === undefined) {
      return "N/A"
    }
    if (tcpi === "overrun") {
      return "overrun"
    }
    return formatIndex(tcpi)
  }

  if (isLoading) {
    return (
      <Box mb={6}>
        <Heading size="md" mb={4}>
          Project Baseline Snapshot
        </Heading>
        <Grid
          templateColumns={{
            base: "1fr",
            md: "repeat(2, 1fr)",
            lg: "repeat(3, 1fr)",
          }}
          gap={4}
        >
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
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

  if (isError || !snapshot) {
    return (
      <Box mb={6}>
        <Heading size="md" mb={4}>
          Project Baseline Snapshot
        </Heading>
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor="red.500"
          bg={cardBg}
        >
          <Text color="red.500">
            Error loading baseline snapshot. Please try again.
          </Text>
        </Box>
      </Box>
    )
  }

  const cpiStatus = getCpiStatus(snapshot.cpi)
  const spiStatus = getSpiStatus(snapshot.spi)
  const tcpiStatus = getTcpiStatus(snapshot.tcpi)
  const cvStatus = getCvStatus(snapshot.cost_variance)
  const svStatus = getSvStatus(snapshot.schedule_variance)

  const CpiIcon = cpiStatus.icon
  const SpiIcon = spiStatus.icon
  const TcpiIcon = tcpiStatus.icon
  const CvIcon = cvStatus.icon
  const SvIcon = svStatus.icon

  return (
    <Box mb={6}>
      <Heading size="md" mb={4}>
        Project Baseline Snapshot
      </Heading>
      <Grid
        templateColumns={{
          base: "1fr",
          md: "repeat(2, 1fr)",
          lg: "repeat(3, 1fr)",
        }}
        gap={4}
      >
        {/* Card 1: Planned Value */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Planned Value (PV)
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(snapshot.planned_value)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Planned Value
            </Text>
          </VStack>
        </Box>

        {/* Card 2: Earned Value */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Earned Value (EV)
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(snapshot.earned_value)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Earned Value
            </Text>
          </VStack>
        </Box>

        {/* Card 3: Actual Cost */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Actual Cost (AC)
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(snapshot.actual_cost)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Actual Cost
            </Text>
          </VStack>
        </Box>

        {/* Card 4: Budget BAC */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Budget at Completion (BAC)
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(snapshot.budget_bac)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Budget BAC
            </Text>
          </VStack>
        </Box>

        {/* Card 5: Estimate at Completion */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="md"
          borderColor={borderCol}
          bg={cardBg}
        >
          <VStack align="stretch" gap={1}>
            <Text fontSize="sm" color={mutedText} fontWeight="medium">
              Estimate at Completion (EAC)
            </Text>
            <Text fontSize="xl" fontWeight="bold">
              {formatCurrency(snapshot.eac)}
            </Text>
            <Text fontSize="xs" color={mutedText} mt={1}>
              Forecast EAC
            </Text>
          </VStack>
        </Box>

        {/* Card 6: Cost Performance Index (CPI) */}
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
              {formatIndex(snapshot.cpi)}
            </Text>
            <Text fontSize="xs" color={cpiStatus.color} mt={1}>
              <CpiIcon style={{ display: "inline", marginRight: "4px" }} />
              {cpiStatus.label}
            </Text>
          </VStack>
        </Box>

        {/* Card 7: Schedule Performance Index (SPI) */}
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
              {formatIndex(snapshot.spi)}
            </Text>
            <Text fontSize="xs" color={spiStatus.color} mt={1}>
              <SpiIcon style={{ display: "inline", marginRight: "4px" }} />
              {spiStatus.label}
            </Text>
          </VStack>
        </Box>

        {/* Card 8: To-Complete Performance Index (TCPI) */}
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
              {formatTcpi(snapshot.tcpi)}
            </Text>
            <Text fontSize="xs" color={tcpiStatus.color} mt={1}>
              <TcpiIcon style={{ display: "inline", marginRight: "4px" }} />
              {tcpiStatus.label}
            </Text>
          </VStack>
        </Box>

        {/* Card 9: Cost Variance (CV) */}
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
              {formatCurrency(snapshot.cost_variance)}
            </Text>
            <Text fontSize="xs" color={cvStatus.color} mt={1}>
              <CvIcon style={{ display: "inline", marginRight: "4px" }} />
              {cvStatus.label}
            </Text>
          </VStack>
        </Box>

        {/* Card 10: Schedule Variance (SV) */}
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
              {formatCurrency(snapshot.schedule_variance)}
            </Text>
            <Text fontSize="xs" color={svStatus.color} mt={1}>
              <SvIcon style={{ display: "inline", marginRight: "4px" }} />
              {svStatus.label}
            </Text>
          </VStack>
        </Box>
      </Grid>
    </Box>
  )
}
