import { Box, Heading, Text, VStack } from "@chakra-ui/react"
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  TimeScale,
  Tooltip,
} from "chart.js"
import "chartjs-adapter-date-fns"
import { useQuery } from "@tanstack/react-query"
import { Line } from "react-chartjs-2"
import {
  type CostElementWithSchedulePublic,
  CostTimelineService,
} from "@/client"
import type { TimePeriod } from "@/utils/progressionCalculations"
import {
  calculateGaussianProgression,
  calculateLinearProgression,
  calculateLogarithmicProgression,
} from "@/utils/progressionCalculations"
import { aggregateTimelines } from "@/utils/timelineAggregation"
import { generateTimeSeries } from "@/utils/timeSeriesGenerator"

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  TimeScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
)

export interface BudgetTimelineProps {
  costElements: CostElementWithSchedulePublic[]
  viewMode?: "aggregated" | "multi-line" // Default: "aggregated"
  displayMode?: "budget" | "costs" | "both" // Default: "budget"
  projectId?: string // Required for cost timeline fetching
  wbeIds?: string[] // Optional filter for cost timeline
  costElementIds?: string[] // Optional filter for cost timeline
}

export default function BudgetTimeline({
  costElements,
  viewMode = "aggregated",
  displayMode = "budget",
  projectId,
  wbeIds,
  costElementIds,
}: BudgetTimelineProps) {
  // Fetch cost timeline data if displayMode includes "costs"
  const shouldFetchCosts = displayMode === "costs" || displayMode === "both"

  // Normalize filter arrays for query key (sort to ensure consistent comparison)
  const normalizedWbeIds = wbeIds?.length ? [...wbeIds].sort() : undefined
  const normalizedCostElementIds = costElementIds?.length
    ? [...costElementIds].sort()
    : undefined

  const { data: costTimelineData, isLoading: isLoadingCosts } = useQuery({
    queryFn: () =>
      CostTimelineService.getProjectCostTimeline({
        projectId: projectId!,
        wbeIds: normalizedWbeIds,
        costElementIds: normalizedCostElementIds,
      }),
    queryKey: [
      "cost-timeline",
      projectId,
      normalizedWbeIds,
      normalizedCostElementIds,
    ],
    enabled: shouldFetchCosts && !!projectId,
  })

  // Filter out cost elements without schedules
  const elementsWithSchedules = costElements.filter(
    (ce) => ce.schedule !== null && ce.schedule !== undefined,
  )

  if (elementsWithSchedules.length === 0) {
    return (
      <Box p={4} borderWidth="1px" borderRadius="lg" bg="bg.surface">
        <Text color="fg.muted">
          No cost elements with schedules selected. Please select cost elements
          that have schedules defined.
        </Text>
      </Box>
    )
  }

  // Calculate timelines for each cost element
  const timelines: TimePeriod[][] = elementsWithSchedules
    .map((ce) => {
      const schedule = ce.schedule!
      const startDate = new Date(schedule.start_date)
      const endDate = new Date(schedule.end_date)
      const budgetBac = Number(ce.budget_bac || 0)

      // Validate dates
      if (
        Number.isNaN(startDate.getTime()) ||
        Number.isNaN(endDate.getTime())
      ) {
        console.warn(
          `Invalid dates for cost element ${ce.cost_element_id}: start=${schedule.start_date}, end=${schedule.end_date}`,
        )
        return null
      }

      // Validate end date >= start date
      if (endDate < startDate) {
        console.warn(
          `End date before start date for cost element ${ce.cost_element_id}`,
        )
        return null
      }

      // Validate budget_bac >= 0
      if (budgetBac < 0) {
        console.warn(
          `Negative budget for cost element ${ce.cost_element_id}: ${budgetBac}`,
        )
        return null
      }

      // Generate time series (daily granularity for now)
      const timePoints = generateTimeSeries(startDate, endDate, "daily")

      // Calculate progression based on progression type
      let progression: TimePeriod[]
      switch (schedule.progression_type) {
        case "linear":
          progression = calculateLinearProgression(
            startDate,
            endDate,
            budgetBac,
            timePoints,
          )
          break
        case "gaussian":
          progression = calculateGaussianProgression(
            startDate,
            endDate,
            budgetBac,
            timePoints,
          )
          break
        case "logarithmic":
          progression = calculateLogarithmicProgression(
            startDate,
            endDate,
            budgetBac,
            timePoints,
          )
          break
        default:
          // Default to linear if unknown type
          progression = calculateLinearProgression(
            startDate,
            endDate,
            budgetBac,
            timePoints,
          )
      }

      return progression
    })
    .filter((timeline): timeline is TimePeriod[] => timeline !== null)

  // Prepare cost timeline data for chart
  const costTimelinePoints = costTimelineData?.data || []
  const costData = costTimelinePoints.map((point) => ({
    x: new Date(point.point_date),
    y: parseFloat(point.cumulative_cost),
  }))

  // Check if we have any valid timelines after filtering
  // Also check if we need budget data (displayMode includes "budget")
  const shouldShowBudget = displayMode === "budget" || displayMode === "both"
  const shouldShowCosts = displayMode === "costs" || displayMode === "both"

  if (shouldShowBudget && timelines.length === 0 && !shouldShowCosts) {
    return (
      <Box p={4} borderWidth="1px" borderRadius="lg" bg="bg.surface">
        <Text color="fg.muted">
          No valid timelines found. Some cost elements may have invalid schedule
          dates or negative budgets.
        </Text>
      </Box>
    )
  }

  if (shouldShowCosts && costData.length === 0 && !shouldShowBudget) {
    return (
      <Box p={4} borderWidth="1px" borderRadius="lg" bg="bg.surface">
        <Text color="fg.muted">
          No cost data available for the selected filters.
        </Text>
      </Box>
    )
  }

  if (
    shouldShowBudget &&
    timelines.length === 0 &&
    shouldShowCosts &&
    costData.length === 0
  ) {
    return (
      <Box p={4} borderWidth="1px" borderRadius="lg" bg="bg.surface">
        <Text color="fg.muted">
          No budget or cost data available for the selected filters.
        </Text>
      </Box>
    )
  }

  // Prepare chart data
  let chartData: any
  let chartOptions: any

  if (viewMode === "aggregated") {
    // Aggregate all timelines into one
    const aggregated = shouldShowBudget ? aggregateTimelines(timelines) : []

    // Build datasets array
    const datasets: any[] = []

    // Add PV (Planned Value) dataset if showing budget
    if (shouldShowBudget && aggregated.length > 0) {
      datasets.push({
        label: "Planned Value (PV)",
        data: aggregated.map((period) => ({
          x: period.date,
          y: period.cumulativeBudget,
        })),
        borderColor: "#3182ce", // blue.500
        backgroundColor: "rgba(49, 130, 206, 0.1)",
        borderWidth: 2,
        fill: false,
      })
    }

    // Add AC (Actual Cost) dataset if showing costs
    if (shouldShowCosts && costData.length > 0) {
      datasets.push({
        label: "Actual Cost (AC)",
        data: costData,
        borderColor: "#f56565", // red.500
        backgroundColor: "transparent",
        borderWidth: 2,
        fill: false,
      })
    }

    // Use combined date range for labels
    const allDates = [
      ...(shouldShowBudget ? aggregated.map((p) => p.date) : []),
      ...(shouldShowCosts
        ? costTimelinePoints.map((p) => new Date(p.point_date))
        : []),
    ]
    const uniqueDates = Array.from(
      new Set(allDates.map((d) => d.getTime())),
    ).map((t) => new Date(t))
    uniqueDates.sort((a, b) => a.getTime() - b.getTime())

    chartData = {
      labels: uniqueDates,
      datasets,
    }

    chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: "index" as const,
      },
      plugins: {
        legend: {
          display: true,
          position: "top" as const,
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const datasetLabel = context.dataset.label || ""
              const value = context.parsed.y
              return `${datasetLabel}: €${value.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`
            },
          },
        },
      },
      scales: {
        x: {
          type: "time" as const,
          time: {
            unit: "day" as const,
            displayFormats: {
              day: "MMM d, yyyy",
            },
          },
          title: {
            display: true,
            text: "Date",
          },
        },
        y: {
          title: {
            display: true,
            text:
              shouldShowBudget && shouldShowCosts
                ? "Cumulative Amount (€)"
                : shouldShowBudget
                  ? "Cumulative Budget (€)"
                  : "Cumulative Cost (€)",
          },
          ticks: {
            callback: (value: number) => {
              return `€${value.toLocaleString("en-US", {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}`
            },
          },
        },
      },
    }
  } else {
    // Multi-line mode: one line per cost element for budget, single line for costs
    const colors = [
      "#3182ce", // blue.500
      "#48bb78", // green.500
      "#ed8936", // orange.500
      "#9f7aea", // purple.500
      "#f56565", // red.500
      "#38b2ac", // teal.500
    ]

    // Build datasets array
    const datasets: any[] = []

    // Add PV (Planned Value) datasets for each cost element if showing budget
    if (shouldShowBudget) {
      elementsWithSchedules.forEach((ce, index) => {
        const timeline = timelines[index]
        if (timeline) {
          datasets.push({
            label: `${ce.department_name} - PV (€${Number(ce.budget_bac).toLocaleString()})`,
            data: timeline.map((period) => ({
              x: period.date,
              y: period.cumulativeBudget,
            })),
            borderColor: colors[index % colors.length],
            backgroundColor: "transparent",
            borderWidth: 2,
            fill: false,
          })
        }
      })
    }

    // Add AC (Actual Cost) dataset if showing costs
    if (shouldShowCosts && costData.length > 0) {
      datasets.push({
        label: "Actual Cost (AC)",
        data: costData,
        borderColor: "#f56565", // red.500
        backgroundColor: "transparent",
        borderWidth: 2,
        fill: false,
      })
    }

    // Use combined date range for labels
    const allDates = [
      ...(shouldShowBudget
        ? timelines.flatMap((timeline) => timeline.map((period) => period.date))
        : []),
      ...(shouldShowCosts
        ? costTimelinePoints.map((p) => new Date(p.point_date))
        : []),
    ]
    const uniqueDates = Array.from(
      new Set(allDates.map((d) => d.getTime())),
    ).map((t) => new Date(t))
    uniqueDates.sort((a, b) => a.getTime() - b.getTime())

    chartData = {
      labels: uniqueDates,
      datasets,
    }

    chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: "index" as const,
      },
      plugins: {
        legend: {
          display: true,
          position: "top" as const,
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const datasetLabel = context.dataset.label || ""
              const value = context.parsed.y
              return `${datasetLabel}: €${value.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`
            },
          },
        },
      },
      scales: {
        x: {
          type: "time" as const,
          time: {
            unit: "day" as const,
            displayFormats: {
              day: "MMM d, yyyy",
            },
          },
          title: {
            display: true,
            text: "Date",
          },
        },
        y: {
          title: {
            display: true,
            text:
              shouldShowBudget && shouldShowCosts
                ? "Cumulative Amount (€)"
                : shouldShowBudget
                  ? "Cumulative Budget (€)"
                  : "Cumulative Cost (€)",
          },
          ticks: {
            callback: (value: number) => {
              return `€${value.toLocaleString("en-US", {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}`
            },
          },
        },
      },
    }
  }

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4} bg="bg.surface" mb={4}>
      <VStack gap={4} align="stretch">
        <Heading size="md">
          {displayMode === "both"
            ? "Budget & Cost Timeline"
            : displayMode === "costs"
              ? "Cost Timeline"
              : "Budget Timeline"}
        </Heading>
        <Box height="400px">
          <Line data={chartData} options={chartOptions} />
        </Box>
        <Text fontSize="sm" color="fg.muted">
          {displayMode === "both" && (
            <>
              Showing {elementsWithSchedules.length} cost element(s) for budget
              {costTimelineData?.data && costTimelineData.data.length > 0 && (
                <>
                  {" "}
                  and {costTimelineData.data.length} cost point(s) for actual
                  costs
                </>
              )}
            </>
          )}
          {displayMode === "budget" && (
            <>
              Showing {elementsWithSchedules.length} cost element(s)
              {viewMode === "aggregated"
                ? " (aggregated)"
                : " (individual lines)"}
            </>
          )}
          {displayMode === "costs" && (
            <>
              Showing {costTimelineData?.data?.length || 0} cost point(s) for
              actual costs
            </>
          )}
        </Text>
      </VStack>
    </Box>
  )
}
