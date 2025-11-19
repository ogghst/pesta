import {
  Badge,
  Box,
  Button,
  Collapsible,
  Container,
  Flex,
  Heading,
  HStack,
  SimpleGrid,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useEffect, useMemo, useState } from "react"
import {
  FiAlertCircle,
  FiChevronDown,
  FiChevronUp,
  FiMinus,
  FiTrendingDown,
  FiTrendingUp,
} from "react-icons/fi"
import {
  AdminService,
  BudgetTimelineService,
  type CostElementTypePublic,
  CostElementTypesService,
  type EVMIndicesProjectPublic,
  EvmMetricsService,
  type ProjectPublic,
  ProjectsService,
  ReportsService,
  type VarianceAnalysisReportPublic,
  type VarianceThresholdConfigPublic,
  type WBEPublic,
  WbesService,
} from "@/client"
import BudgetTimeline from "@/components/Projects/BudgetTimeline"
import { Checkbox } from "@/components/ui/checkbox"
import { useColorModeValue } from "@/components/ui/color-mode"
import { useTimeMachine } from "@/context/TimeMachineContext"

export interface ProjectPerformanceDashboardProps {
  projectId: string
}

export default function ProjectPerformanceDashboard({
  projectId,
}: ProjectPerformanceDashboardProps) {
  const [activeProjectId, setActiveProjectId] = useState(projectId)
  const [selectedWbeIds, setSelectedWbeIds] = useState<string[]>([])
  const [selectedCostElementTypeIds, setSelectedCostElementTypeIds] = useState<
    string[]
  >([])

  useEffect(() => {
    setActiveProjectId(projectId)
  }, [projectId])

  useEffect(() => {
    setSelectedWbeIds([])
    setSelectedCostElementTypeIds([])
  }, [])

  const { data: projectList } = useQuery({
    queryKey: ["projects", "dashboard-picker"],
    queryFn: () =>
      ProjectsService.readProjects({
        skip: 0,
        limit: 50,
      }),
    staleTime: 5 * 60 * 1000,
  })

  const { data: projectDetail } = useQuery({
    queryKey: ["project", activeProjectId],
    queryFn: () => ProjectsService.readProject({ id: activeProjectId }),
    enabled: !!activeProjectId,
  })

  const {
    data: wbeResponse,
    isLoading: isLoadingWbes,
    isFetching: isFetchingWbes,
  } = useQuery({
    queryKey: ["dashboard-wbes", activeProjectId],
    queryFn: () =>
      WbesService.readWbes({
        projectId: activeProjectId,
        skip: 0,
        limit: 1000,
      }),
    enabled: !!activeProjectId,
  })

  const wbes = wbeResponse?.data ?? []

  // Fetch cost element types for filtering
  const { data: costElementTypesData } = useQuery({
    queryKey: ["cost-element-types"],
    queryFn: () => CostElementTypesService.readCostElementTypes(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  })

  const costElementTypes =
    costElementTypesData?.data?.filter((type) => type.is_active) ?? []

  const projectOptions = useMemo(() => {
    const base = projectList?.data ?? []
    const exists = base.some((proj) => proj.project_id === activeProjectId)
    if (!exists && activeProjectId) {
      if (projectDetail) {
        return [...base, projectDetail as ProjectPublic]
      }
      return [
        ...base,
        {
          project_id: activeProjectId,
          project_name: `Project ${activeProjectId.slice(0, 4)}`,
        } as ProjectPublic,
      ]
    }
    return base
  }, [projectList?.data, projectDetail, activeProjectId])

  const wbeLookup = useMemo(() => {
    const lookup: Record<string, string> = {}
    for (const wbe of wbes) {
      lookup[wbe.wbe_id] = wbe.machine_type || `WBE ${wbe.wbe_id.slice(0, 4)}`
    }
    return lookup
  }, [wbes])

  // Filter by cost element types - users can filter independently by WBE and/or cost element type

  const { controlDate } = useTimeMachine()

  // Normalize filter arrays for consistent query key comparison
  const normalizedWbeIds = useMemo(() => {
    return selectedWbeIds.length > 0 ? [...selectedWbeIds].sort() : undefined
  }, [selectedWbeIds])

  const normalizedCostElementTypeIds = useMemo(() => {
    return selectedCostElementTypeIds.length > 0
      ? [...selectedCostElementTypeIds].sort()
      : undefined
  }, [selectedCostElementTypeIds])

  // Fetch cost elements with schedules for BudgetTimeline
  const { data: costElementsWithSchedules, isLoading: isLoadingTimeline } =
    useQuery({
      queryFn: () =>
        BudgetTimelineService.getCostElementsWithSchedules({
          projectId: activeProjectId,
          wbeIds: normalizedWbeIds,
          costElementTypeIds: normalizedCostElementTypeIds,
        }),
      queryKey: [
        "cost-elements-with-schedules",
        activeProjectId,
        normalizedWbeIds,
        normalizedCostElementTypeIds,
        controlDate,
      ],
      enabled: !!activeProjectId,
    })

  // Fetch EVM metrics for project
  const { data: evmMetrics, isLoading: isLoadingEvmMetrics } =
    useQuery<EVMIndicesProjectPublic>({
      queryKey: ["evm-metrics", "project", activeProjectId, controlDate],
      queryFn: () =>
        EvmMetricsService.getProjectEvmMetricsEndpoint({
          projectId: activeProjectId,
        }),
      enabled: !!activeProjectId,
    })

  // Fetch earned value to get BAC for CV/SV percentage calculation
  const { data: earnedValue } = useQuery({
    queryKey: ["earned-value", "project", activeProjectId, controlDate],
    queryFn: async () => {
      const { EarnedValueService } = await import("@/client")
      return EarnedValueService.getProjectEarnedValue({
        projectId: activeProjectId,
      })
    },
    enabled: !!activeProjectId,
  })

  // Fetch variance thresholds (with error handling for non-admin users)
  const { data: varianceThresholds, isLoading: isLoadingThresholds } = useQuery<
    VarianceThresholdConfigPublic[]
  >({
    queryKey: ["variance-threshold-configs"],
    queryFn: async () => {
      try {
        const response = await AdminService.listVarianceThresholdConfigs()
        return response.data.filter((config) => config.is_active)
      } catch (_error) {
        // If user is not admin, return empty array (will use hardcoded thresholds)
        return []
      }
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  })

  const clearFilters = () => {
    setSelectedWbeIds([])
    setSelectedCostElementTypeIds([])
  }

  // Theme-aware colors
  const cardBg = useColorModeValue("bg.surface", "bg.surface")
  const borderCol = useColorModeValue("border", "border")
  const mutedText = useColorModeValue("fg.muted", "fg.muted")

  // Formatting helpers
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

  // Build threshold lookup from config
  const thresholdLookup = useMemo(() => {
    const lookup: Record<string, number> = {}
    if (varianceThresholds) {
      for (const config of varianceThresholds) {
        lookup[config.threshold_type] = Number(config.threshold_percentage)
      }
    }
    return lookup
  }, [varianceThresholds])

  // Status indicator type
  type StatusIndicator = {
    color: string
    icon: typeof FiTrendingUp
    label: string
  }

  // Status helpers (reusing logic from EarnedValueSummary)
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

  const getTcpiStatus = (tcpi: string | null | undefined): StatusIndicator => {
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
    const numValue = Number(tcpi)
    if (Number.isNaN(numValue)) {
      return {
        color: "gray.500",
        icon: FiMinus,
        label: "N/A",
      }
    }
    if (numValue <= 1.0) {
      return {
        color: "green.500",
        icon: FiTrendingUp,
        label: "On Track",
      }
    }
    if (numValue <= 1.1) {
      return {
        color: "yellow.500",
        icon: FiMinus,
        label: "At Risk",
      }
    }
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Over Target",
    }
  }

  // CV/SV status with configurable thresholds
  const getCvStatus = (
    cv: string | number | null | undefined,
    bac: number | null | undefined,
  ): StatusIndicator => {
    if (cv === null || cv === undefined || bac === null || bac === undefined) {
      return {
        color: "gray.500",
        icon: FiMinus,
        label: "N/A",
      }
    }
    const numValue = typeof cv === "string" ? Number(cv) : cv
    if (Number.isNaN(numValue) || bac === 0) {
      return {
        color: "gray.500",
        icon: FiMinus,
        label: "N/A",
      }
    }

    // Calculate percentage variance
    const cvPercentage = (numValue / bac) * 100

    // Use configurable thresholds if available
    const criticalThreshold = thresholdLookup.critical_cv ?? -10.0
    const warningThreshold = thresholdLookup.warning_cv ?? -5.0

    if (cvPercentage <= criticalThreshold) {
      return {
        color: "red.500",
        icon: FiTrendingDown,
        label: "Critical Over Budget",
      }
    }
    if (cvPercentage <= warningThreshold) {
      return {
        color: "orange.500",
        icon: FiTrendingDown,
        label: "Over Budget",
      }
    }
    if (numValue < 0) {
      return {
        color: "yellow.500",
        icon: FiTrendingDown,
        label: "Slightly Over",
      }
    }
    if (numValue === 0) {
      return {
        color: "yellow.500",
        icon: FiMinus,
        label: "On Budget",
      }
    }
    return {
      color: "green.500",
      icon: FiTrendingUp,
      label: "Under Budget",
    }
  }

  const getSvStatus = (
    sv: string | number | null | undefined,
    bac: number | null | undefined,
  ): StatusIndicator => {
    if (sv === null || sv === undefined || bac === null || bac === undefined) {
      return {
        color: "gray.500",
        icon: FiMinus,
        label: "N/A",
      }
    }
    const numValue = typeof sv === "string" ? Number(sv) : sv
    if (Number.isNaN(numValue) || bac === 0) {
      return {
        color: "gray.500",
        icon: FiMinus,
        label: "N/A",
      }
    }

    // Calculate percentage variance
    const svPercentage = (numValue / bac) * 100

    // Use configurable thresholds if available
    const warningThreshold = thresholdLookup.warning_sv ?? -3.0

    if (svPercentage <= warningThreshold) {
      return {
        color: "red.500",
        icon: FiTrendingDown,
        label: "Behind Schedule",
      }
    }
    if (numValue < 0) {
      return {
        color: "orange.500",
        icon: FiTrendingDown,
        label: "Slightly Behind",
      }
    }
    if (numValue === 0) {
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

  // Get EVM metrics
  const cpi = evmMetrics?.cpi
  const spi = evmMetrics?.spi
  const tcpi = evmMetrics?.tcpi
  const costVariance = evmMetrics?.cost_variance
  const scheduleVariance = evmMetrics?.schedule_variance

  // Get BAC from earned value for CV/SV percentage calculation
  const bac = earnedValue?.budget_bac ? Number(earnedValue.budget_bac) : null

  // Status indicators
  const cpiStatus = getCpiStatus(cpi)
  const spiStatus = getSpiStatus(spi)
  const tcpiStatus = getTcpiStatus(tcpi)
  const cvStatus = getCvStatus(costVariance, bac)
  const svStatus = getSvStatus(scheduleVariance, bac)

  // Icon components
  const CpiIcon = cpiStatus.icon
  const SpiIcon = spiStatus.icon
  const TcpiIcon = tcpiStatus.icon
  const CvIcon = cvStatus.icon
  const SvIcon = svStatus.icon

  const isLoadingKpis = isLoadingEvmMetrics || isLoadingThresholds

  // Fetch variance analysis report for drilldown deck
  const { data: varianceReport, isLoading: isLoadingDrilldown } =
    useQuery<VarianceAnalysisReportPublic>({
      queryKey: [
        "variance-analysis-report",
        "drilldown",
        activeProjectId,
        normalizedWbeIds,
        normalizedCostElementTypeIds,
        controlDate,
      ],
      queryFn: () =>
        ReportsService.getProjectVarianceAnalysisReportEndpoint({
          projectId: activeProjectId,
          showOnlyProblems: true,
          sortBy: "cv",
        }),
      enabled: !!activeProjectId,
    })

  // Filter and limit drilldown items
  const drilldownItems = useMemo(() => {
    if (!varianceReport?.rows) {
      return []
    }
    let items = varianceReport.rows

    // Apply WBE filter if selected
    if (normalizedWbeIds && normalizedWbeIds.length > 0) {
      items = items.filter((row) => normalizedWbeIds.includes(row.wbe_id))
    }

    // Apply cost element type filter if selected
    if (
      normalizedCostElementTypeIds &&
      normalizedCostElementTypeIds.length > 0
    ) {
      items = items.filter(
        (row) =>
          row.cost_element_type_id &&
          normalizedCostElementTypeIds.includes(row.cost_element_type_id),
      )
    }

    // Return top 10 items (already sorted by variance from API)
    return items.slice(0, 10)
  }, [varianceReport?.rows, normalizedWbeIds, normalizedCostElementTypeIds])

  // Extract cost element IDs from filtered cost elements for BudgetTimeline
  // This ensures actual cost timeline is filtered consistently with planned value and earned value
  const costElementIdsForTimeline = useMemo(() => {
    if (!costElementsWithSchedules || costElementsWithSchedules.length === 0) {
      return undefined
    }
    const ids = costElementsWithSchedules
      .map((ce) => ce.cost_element_id)
      .filter(Boolean) as string[]
    return ids.length > 0 ? ids.sort() : undefined
  }, [costElementsWithSchedules])

  const navigate = useNavigate()

  return (
    <Container maxW="full" py={8}>
      <Stack gap={6}>
        <Stack gap={3}>
          <Heading size="lg">Project Performance Dashboard</Heading>
          <Text color="fg.muted">
            Snapshot for project{" "}
            <strong>
              {projectDetail?.project_name ?? activeProjectId ?? "—"}
            </strong>
          </Text>
        </Stack>

        <FiltersCard
          projectOptions={projectOptions}
          selectedProjectId={activeProjectId}
          onProjectChange={setActiveProjectId}
          wbes={wbes}
          selectedWbeIds={selectedWbeIds}
          onWbeChange={setSelectedWbeIds}
          costElementTypes={costElementTypes}
          selectedCostElementTypeIds={selectedCostElementTypeIds}
          onCostElementTypeChange={setSelectedCostElementTypeIds}
          wbeLookup={wbeLookup}
          isLoading={isLoadingWbes || isFetchingWbes}
          onClearFilters={clearFilters}
        />

        <Stack gap={4}>
          <Heading size="md">Timeline Overview</Heading>
          {isLoadingTimeline ? (
            <PlaceholderPanel label="Loading timeline data..." />
          ) : !costElementsWithSchedules ||
            costElementsWithSchedules.length === 0 ? (
            <PlaceholderPanel label="No timeline data available for selected filters" />
          ) : (
            <BudgetTimeline
              costElements={costElementsWithSchedules}
              viewMode="aggregated"
              projectId={activeProjectId}
              wbeIds={normalizedWbeIds}
              costElementIds={costElementIdsForTimeline}
            />
          )}
        </Stack>

        <Stack gap={4}>
          <Heading size="md">Performance KPIs</Heading>
          {isLoadingKpis ? (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4}>
              {[1, 2, 3, 4].map((i) => (
                <Box
                  key={i}
                  borderWidth="1px"
                  borderRadius="lg"
                  px={4}
                  py={6}
                  bg={cardBg}
                  borderColor={borderCol}
                >
                  <Text fontSize="sm" color={mutedText}>
                    Loading...
                  </Text>
                </Box>
              ))}
            </SimpleGrid>
          ) : (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4}>
              {/* CPI Card */}
              <Box
                borderWidth="1px"
                borderRadius="lg"
                px={4}
                py={4}
                bg={cardBg}
                borderColor={borderCol}
              >
                <VStack align="stretch" gap={1}>
                  <Text fontSize="sm" color={mutedText} fontWeight="medium">
                    Cost Performance Index (CPI)
                  </Text>
                  <Box display="flex" alignItems="center" gap={2}>
                    <CpiIcon color={cpiStatus.color} />
                    <Heading size="md" color={cpiStatus.color}>
                      {formatIndex(cpi)}
                    </Heading>
                  </Box>
                  <Text fontSize="xs" color={mutedText} mt={1}>
                    {cpiStatus.label}
                  </Text>
                </VStack>
              </Box>

              {/* SPI Card */}
              <Box
                borderWidth="1px"
                borderRadius="lg"
                px={4}
                py={4}
                bg={cardBg}
                borderColor={borderCol}
              >
                <VStack align="stretch" gap={1}>
                  <Text fontSize="sm" color={mutedText} fontWeight="medium">
                    Schedule Performance Index (SPI)
                  </Text>
                  <Box display="flex" alignItems="center" gap={2}>
                    <SpiIcon color={spiStatus.color} />
                    <Heading size="md" color={spiStatus.color}>
                      {formatIndex(spi)}
                    </Heading>
                  </Box>
                  <Text fontSize="xs" color={mutedText} mt={1}>
                    {spiStatus.label}
                  </Text>
                </VStack>
              </Box>

              {/* TCPI Card */}
              <Box
                borderWidth="1px"
                borderRadius="lg"
                px={4}
                py={4}
                bg={cardBg}
                borderColor={borderCol}
              >
                <VStack align="stretch" gap={1}>
                  <Text fontSize="sm" color={mutedText} fontWeight="medium">
                    To-Complete Performance Index (TCPI)
                  </Text>
                  <Box display="flex" alignItems="center" gap={2}>
                    <TcpiIcon color={tcpiStatus.color} />
                    <Heading size="md" color={tcpiStatus.color}>
                      {tcpi === "overrun" ? "overrun" : formatIndex(tcpi)}
                    </Heading>
                  </Box>
                  <Text fontSize="xs" color={mutedText} mt={1}>
                    {tcpiStatus.label}
                  </Text>
                </VStack>
              </Box>

              {/* CV Card */}
              <Box
                borderWidth="1px"
                borderRadius="lg"
                px={4}
                py={4}
                bg={cardBg}
                borderColor={borderCol}
              >
                <VStack align="stretch" gap={1}>
                  <Text fontSize="sm" color={mutedText} fontWeight="medium">
                    Cost Variance (CV)
                  </Text>
                  <Box display="flex" alignItems="center" gap={2}>
                    <CvIcon color={cvStatus.color} />
                    <Heading size="md" color={cvStatus.color}>
                      {formatCurrency(costVariance)}
                    </Heading>
                  </Box>
                  <Text fontSize="xs" color={mutedText} mt={1}>
                    {cvStatus.label}
                  </Text>
                </VStack>
              </Box>

              {/* SV Card */}
              <Box
                borderWidth="1px"
                borderRadius="lg"
                px={4}
                py={4}
                bg={cardBg}
                borderColor={borderCol}
              >
                <VStack align="stretch" gap={1}>
                  <Text fontSize="sm" color={mutedText} fontWeight="medium">
                    Schedule Variance (SV)
                  </Text>
                  <Box display="flex" alignItems="center" gap={2}>
                    <SvIcon color={svStatus.color} />
                    <Heading size="md" color={svStatus.color}>
                      {formatCurrency(scheduleVariance)}
                    </Heading>
                  </Box>
                  <Text fontSize="xs" color={mutedText} mt={1}>
                    {svStatus.label}
                  </Text>
                </VStack>
              </Box>
            </SimpleGrid>
          )}
        </Stack>

        <Stack gap={4}>
          <Heading size="md">Drilldown Focus</Heading>
          {isLoadingDrilldown ? (
            <PlaceholderPanel label="Loading drilldown data..." />
          ) : drilldownItems.length === 0 ? (
            <PlaceholderPanel label="No variance issues found for selected filters" />
          ) : (
            <Box
              borderWidth="1px"
              borderRadius="lg"
              overflow="hidden"
              bg={cardBg}
              borderColor={borderCol}
            >
              <Box overflowX="auto">
                <Box
                  as="table"
                  width="100%"
                  style={{ borderCollapse: "collapse" }}
                >
                  <Box as="thead" bg="bg.subtle">
                    <Box as="tr">
                      <Box
                        as="th"
                        px={4}
                        py={3}
                        textAlign="left"
                        fontSize="sm"
                        fontWeight="semibold"
                        color={mutedText}
                        borderBottomWidth="1px"
                        borderColor={borderCol}
                      >
                        WBE
                      </Box>
                      <Box
                        as="th"
                        px={4}
                        py={3}
                        textAlign="left"
                        fontSize="sm"
                        fontWeight="semibold"
                        color={mutedText}
                        borderBottomWidth="1px"
                        borderColor={borderCol}
                      >
                        Cost Element
                      </Box>
                      <Box
                        as="th"
                        px={4}
                        py={3}
                        textAlign="left"
                        fontSize="sm"
                        fontWeight="semibold"
                        color={mutedText}
                        borderBottomWidth="1px"
                        borderColor={borderCol}
                      >
                        Cost Element Type
                      </Box>
                      <Box
                        as="th"
                        px={4}
                        py={3}
                        textAlign="right"
                        fontSize="sm"
                        fontWeight="semibold"
                        color={mutedText}
                        borderBottomWidth="1px"
                        borderColor={borderCol}
                      >
                        Cost Variance
                      </Box>
                      <Box
                        as="th"
                        px={4}
                        py={3}
                        textAlign="right"
                        fontSize="sm"
                        fontWeight="semibold"
                        color={mutedText}
                        borderBottomWidth="1px"
                        borderColor={borderCol}
                      >
                        Schedule Variance
                      </Box>
                      <Box
                        as="th"
                        px={4}
                        py={3}
                        textAlign="center"
                        fontSize="sm"
                        fontWeight="semibold"
                        color={mutedText}
                        borderBottomWidth="1px"
                        borderColor={borderCol}
                      >
                        Severity
                      </Box>
                    </Box>
                  </Box>
                  <Box as="tbody">
                    {drilldownItems.map((row) => {
                      const cvNum =
                        typeof row.cost_variance === "string"
                          ? Number(row.cost_variance)
                          : (row.cost_variance ?? 0)
                      const svNum =
                        typeof row.schedule_variance === "string"
                          ? Number(row.schedule_variance)
                          : (row.schedule_variance ?? 0)
                      const cvColor =
                        cvNum < 0
                          ? "red.500"
                          : cvNum === 0
                            ? "gray.500"
                            : "green.500"
                      const svColor =
                        svNum < 0
                          ? "red.500"
                          : svNum === 0
                            ? "gray.500"
                            : "green.500"
                      const severityColor =
                        row.variance_severity === "critical"
                          ? "red.500"
                          : row.variance_severity === "warning"
                            ? "orange.500"
                            : "gray.500"

                      return (
                        <Box
                          as="tr"
                          key={`${row.wbe_id}-${row.cost_element_id}`}
                          _hover={{ bg: "bg.subtle" }}
                          cursor="pointer"
                          onClick={() => {
                            navigate({
                              to: "/projects/$id/wbes/$wbeId/cost-elements/$costElementId",
                              params: {
                                id: activeProjectId,
                                wbeId: row.wbe_id,
                                costElementId: row.cost_element_id,
                              },
                              search: (prev) => ({
                                ...prev,
                                page: prev.page ?? 1,
                                tab: (prev.tab ?? "metrics") as
                                  | "summary"
                                  | "info"
                                  | "cost-summary"
                                  | "metrics"
                                  | "timeline",
                                view: "metrics" as const,
                              }),
                            })
                          }}
                        >
                          <Box
                            as="td"
                            px={4}
                            py={3}
                            borderBottomWidth="1px"
                            borderColor={borderCol}
                          >
                            <Text
                              color="blue.500"
                              _hover={{ textDecoration: "underline" }}
                              cursor="pointer"
                              onClick={(e) => {
                                e.stopPropagation()
                                navigate({
                                  to: "/projects/$id/wbes/$wbeId",
                                  params: {
                                    id: activeProjectId,
                                    wbeId: row.wbe_id,
                                  },
                                  search: {} as any,
                                })
                              }}
                            >
                              {row.wbe_name || row.wbe_id.slice(0, 8)}
                            </Text>
                          </Box>
                          <Box
                            as="td"
                            px={4}
                            py={3}
                            borderBottomWidth="1px"
                            borderColor={borderCol}
                          >
                            <Text>
                              {row.department_name ||
                                row.department_code ||
                                row.cost_element_id.slice(0, 8)}
                            </Text>
                          </Box>
                          <Box
                            as="td"
                            px={4}
                            py={3}
                            borderBottomWidth="1px"
                            borderColor={borderCol}
                          >
                            <Text color={mutedText} fontSize="sm">
                              {row.cost_element_type_name || "—"}
                            </Text>
                          </Box>
                          <Box
                            as="td"
                            px={4}
                            py={3}
                            textAlign="right"
                            borderBottomWidth="1px"
                            borderColor={borderCol}
                          >
                            <Text color={cvColor} fontWeight="medium">
                              {formatCurrency(row.cost_variance)}
                            </Text>
                          </Box>
                          <Box
                            as="td"
                            px={4}
                            py={3}
                            textAlign="right"
                            borderBottomWidth="1px"
                            borderColor={borderCol}
                          >
                            <Text color={svColor} fontWeight="medium">
                              {formatCurrency(row.schedule_variance)}
                            </Text>
                          </Box>
                          <Box
                            as="td"
                            px={4}
                            py={3}
                            textAlign="center"
                            borderBottomWidth="1px"
                            borderColor={borderCol}
                          >
                            <Text
                              fontSize="xs"
                              fontWeight="semibold"
                              color={severityColor}
                              textTransform="uppercase"
                            >
                              {row.variance_severity || "—"}
                            </Text>
                          </Box>
                        </Box>
                      )
                    })}
                  </Box>
                </Box>
              </Box>
            </Box>
          )}
        </Stack>
      </Stack>
    </Container>
  )
}

interface FiltersCardProps {
  projectOptions: ProjectPublic[]
  selectedProjectId: string
  onProjectChange: (id: string) => void
  wbes: WBEPublic[]
  selectedWbeIds: string[]
  onWbeChange: (ids: string[]) => void
  costElementTypes: CostElementTypePublic[]
  selectedCostElementTypeIds: string[]
  onCostElementTypeChange: (ids: string[]) => void
  wbeLookup: Record<string, string>
  isLoading: boolean
  onClearFilters: () => void
}

function FiltersCard({
  projectOptions,
  selectedProjectId,
  onProjectChange,
  wbes,
  selectedWbeIds,
  onWbeChange,
  costElementTypes,
  selectedCostElementTypeIds,
  onCostElementTypeChange,
  wbeLookup,
  isLoading,
  onClearFilters,
}: FiltersCardProps) {
  const hasFiltersApplied =
    selectedWbeIds.length > 0 || selectedCostElementTypeIds.length > 0
  const [isWbeSectionOpen, setIsWbeSectionOpen] = useState(false)
  const [isCostElementTypeSectionOpen, setIsCostElementTypeSectionOpen] =
    useState(false)

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4} bg="bg.surface">
      <Heading size="sm" mb={3}>
        Project & Filters
      </Heading>
      <Stack gap={4}>
        <Box>
          <label htmlFor="dashboard-project-select">
            <Text fontWeight="medium" mb={2} display="block">
              Project
            </Text>
          </label>
          <select
            id="dashboard-project-select"
            value={selectedProjectId}
            onChange={(event) => onProjectChange(event.target.value)}
            style={{
              width: "100%",
              padding: "8px",
              borderRadius: "4px",
              border: "1px solid var(--chakra-colors-border)",
            }}
          >
            {projectOptions.map((project) => (
              <option key={project.project_id} value={project.project_id}>
                {project.project_name}
              </option>
            ))}
          </select>
        </Box>

        {/* Collapsible WBE Filter Section */}
        <Box borderWidth="1px" borderRadius="md" borderColor="border.subtle">
          <Collapsible.Root
            open={isWbeSectionOpen}
            onOpenChange={(event) => setIsWbeSectionOpen(event.open)}
          >
            <Collapsible.Trigger asChild>
              <Button
                variant="ghost"
                justifyContent="space-between"
                width="100%"
                px={4}
                py={3}
              >
                <Flex justify="space-between" align="center" width="100%">
                  <HStack gap={2} align="center">
                    {isWbeSectionOpen ? <FiChevronUp /> : <FiChevronDown />}
                    <Text fontWeight="medium">Work Breakdown Elements</Text>
                  </HStack>
                  <Text fontSize="sm" color="fg.muted">
                    {selectedWbeIds.length > 0
                      ? `${selectedWbeIds.length} selected`
                      : "None selected"}
                  </Text>
                </Flex>
              </Button>
            </Collapsible.Trigger>
            <Collapsible.Content>
              <Box px={4} pb={4}>
                {isLoading ? (
                  <Text color="fg.muted">Loading filters...</Text>
                ) : wbes.length === 0 ? (
                  <Text color="fg.muted">
                    No WBEs available for this project.
                  </Text>
                ) : (
                  <Stack gap={1}>
                    {wbes.map((wbe) => {
                      const isChecked = selectedWbeIds.includes(wbe.wbe_id)
                      return (
                        <Checkbox
                          key={wbe.wbe_id}
                          checked={isChecked}
                          onCheckedChange={({ checked }) => {
                            if (checked) {
                              onWbeChange([...selectedWbeIds, wbe.wbe_id])
                            } else {
                              onWbeChange(
                                selectedWbeIds.filter(
                                  (id) => id !== wbe.wbe_id,
                                ),
                              )
                            }
                          }}
                        >
                          {wbeLookup[wbe.wbe_id]}
                        </Checkbox>
                      )
                    })}
                  </Stack>
                )}
              </Box>
            </Collapsible.Content>
          </Collapsible.Root>
        </Box>

        {/* Collapsible Cost Element Type Filter Section */}
        <Box borderWidth="1px" borderRadius="md" borderColor="border.subtle">
          <Collapsible.Root
            open={isCostElementTypeSectionOpen}
            onOpenChange={(event) =>
              setIsCostElementTypeSectionOpen(event.open)
            }
          >
            <Collapsible.Trigger asChild>
              <Button
                variant="ghost"
                justifyContent="space-between"
                width="100%"
                px={4}
                py={3}
              >
                <Flex justify="space-between" align="center" width="100%">
                  <HStack gap={2} align="center">
                    {isCostElementTypeSectionOpen ? (
                      <FiChevronUp />
                    ) : (
                      <FiChevronDown />
                    )}
                    <Text fontWeight="medium">Cost Element Types</Text>
                  </HStack>
                  <Text fontSize="sm" color="fg.muted">
                    {selectedCostElementTypeIds.length > 0
                      ? `${selectedCostElementTypeIds.length} selected`
                      : "None selected"}
                  </Text>
                </Flex>
              </Button>
            </Collapsible.Trigger>
            <Collapsible.Content>
              <Box px={4} pb={4}>
                <VStack align="stretch" gap={3}>
                  <HStack justify="space-between" align="center">
                    <Text fontSize="sm" fontWeight="medium">
                      Filter by type
                    </Text>
                    <Button
                      size="xs"
                      variant="ghost"
                      onClick={() => {
                        if (
                          selectedCostElementTypeIds.length ===
                          costElementTypes.length
                        ) {
                          onCostElementTypeChange([])
                        } else {
                          onCostElementTypeChange(
                            costElementTypes.map(
                              (type) => type.cost_element_type_id,
                            ),
                          )
                        }
                      }}
                    >
                      {selectedCostElementTypeIds.length ===
                      costElementTypes.length
                        ? "Deselect All"
                        : "Select All"}
                    </Button>
                  </HStack>
                  {costElementTypes.length === 0 ? (
                    <Text fontSize="sm" color="fg.muted">
                      No cost element types found
                    </Text>
                  ) : (
                    <Flex gap={2} flexWrap="wrap">
                      {costElementTypes.map((type) => {
                        const isSelected = selectedCostElementTypeIds.includes(
                          type.cost_element_type_id,
                        )
                        return (
                          <Badge
                            key={type.cost_element_type_id}
                            colorPalette={isSelected ? "blue" : "gray"}
                            cursor="pointer"
                            onClick={() => {
                              if (isSelected) {
                                onCostElementTypeChange(
                                  selectedCostElementTypeIds.filter(
                                    (id) => id !== type.cost_element_type_id,
                                  ),
                                )
                              } else {
                                onCostElementTypeChange([
                                  ...selectedCostElementTypeIds,
                                  type.cost_element_type_id,
                                ])
                              }
                            }}
                            px={3}
                            py={1}
                            _hover={{
                              opacity: 0.8,
                            }}
                          >
                            {type.type_name}
                          </Badge>
                        )
                      })}
                    </Flex>
                  )}
                </VStack>
              </Box>
            </Collapsible.Content>
          </Collapsible.Root>
        </Box>

        <Button
          variant="outline"
          onClick={onClearFilters}
          disabled={!hasFiltersApplied}
          alignSelf="flex-start"
        >
          Clear Filters
        </Button>
      </Stack>
    </Box>
  )
}

function PlaceholderPanel({ label }: { label: string }) {
  return (
    <Box
      borderWidth="1px"
      borderRadius="lg"
      px={4}
      py={6}
      bg="bg.surface"
      textAlign="center"
    >
      <Text color="fg.muted" fontSize="sm">
        {label}
      </Text>
    </Box>
  )
}
