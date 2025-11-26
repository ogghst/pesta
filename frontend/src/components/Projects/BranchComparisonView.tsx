import { Box, Grid, Heading, Text, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { BranchComparisonService } from "@/client"
import type {
  BranchComparisonChange,
  BranchComparisonResponse,
} from "@/types/branchComparison"

interface BranchComparisonViewProps {
  projectId: string
  branch: string
  baseBranch?: string
}

const BranchComparisonView = ({
  projectId,
  branch,
  baseBranch = "main",
}: BranchComparisonViewProps) => {
  const { data, isLoading, error } = useQuery<BranchComparisonResponse>({
    queryKey: ["branch-comparison", projectId, branch, baseBranch],
    queryFn: async () => {
      const response = await BranchComparisonService.compareBranches({
        projectId,
        branch,
        baseBranch,
      })
      return response as unknown as BranchComparisonResponse
    },
    enabled: !!projectId && !!branch && branch !== baseBranch,
  })

  if (isLoading) {
    return (
      <Box p={4}>
        <Text>Loading comparison...</Text>
      </Box>
    )
  }

  if (error) {
    return (
      <Box p={4}>
        <Text color="red.500">Error loading comparison: {String(error)}</Text>
      </Box>
    )
  }

  if (!data) {
    return (
      <Box p={4}>
        <Text>No comparison data available</Text>
      </Box>
    )
  }

  const summary = data.summary
  const creates = data.creates ?? []
  const updates = data.updates ?? []
  const deletes = data.deletes ?? []

  const legacyFinancialImpact = data.financial_impact
  const totalRevenueChange =
    summary?.total_revenue_change ??
    (legacyFinancialImpact
      ? Number(legacyFinancialImpact.total_revenue_change)
      : 0)
  const totalBudgetChange =
    summary?.total_budget_change ??
    (legacyFinancialImpact
      ? Number(legacyFinancialImpact.total_budget_change)
      : 0)

  const formatCurrency = (value: number) => {
    const sign = value > 0 ? "+" : value < 0 ? "-" : ""
    return `${sign}€${Math.abs(value).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  const renderChangeList = (
    items: BranchComparisonChange[],
    accent: "green" | "yellow" | "red",
  ) => {
    if (items.length === 0) {
      return (
        <Text fontSize="sm" color="fg.muted">
          No items
        </Text>
      )
    }

    return (
      <VStack gap={2} align="stretch">
        {items.map((item) => (
          <Box
            key={item.entity_id}
            p={2}
            bg="white"
            borderRadius="md"
            borderWidth="1px"
            borderColor={`${accent}.300`}
          >
            <Text fontSize="sm" fontWeight="medium">
              {item.description}
            </Text>
            {typeof item.revenue_change === "number" && (
              <Text fontSize="xs" color="fg.muted">
                Revenue Δ: {formatCurrency(item.revenue_change)}
              </Text>
            )}
            {typeof item.budget_change === "number" && (
              <Text fontSize="xs" color="fg.muted">
                Budget Δ: {formatCurrency(item.budget_change)}
              </Text>
            )}
          </Box>
        ))}
      </VStack>
    )
  }

  return (
    <Box p={4}>
      <VStack gap={4} align="stretch">
        <Heading size="md">
          Branch Comparison: {branch} vs {baseBranch}
        </Heading>

        {/* Financial Impact Summary */}
        <Box
          p={4}
          borderWidth="1px"
          borderRadius="lg"
          bg="bg.surface"
          borderColor="border.emphasized"
        >
          <Heading size="sm" mb={2}>
            Financial Impact Summary
          </Heading>
          <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4}>
            <Box>
              <Text fontSize="sm" color="fg.muted">
                Total Revenue Change
              </Text>
              <Text
                fontSize="lg"
                fontWeight="bold"
                color={totalRevenueChange >= 0 ? "green.500" : "red.500"}
              >
                {formatCurrency(totalRevenueChange)}
              </Text>
            </Box>
            <Box>
              <Text fontSize="sm" color="fg.muted">
                Total Budget Change
              </Text>
              <Text
                fontSize="lg"
                fontWeight="bold"
                color={totalBudgetChange >= 0 ? "green.500" : "red.500"}
              >
                {formatCurrency(totalBudgetChange)}
              </Text>
            </Box>
          </Grid>
        </Box>

        {/* Side-by-side comparison */}
        <Grid templateColumns={{ base: "1fr", lg: "repeat(2, 1fr)" }} gap={4}>
          {/* Creates */}
          <Box
            p={4}
            borderWidth="1px"
            borderRadius="lg"
            bg="green.50"
            borderColor="green.200"
          >
            <Heading size="sm" mb={2} color="green.700">
              Creates ({creates.length})
            </Heading>
            {renderChangeList(creates, "green")}
          </Box>

          {/* Updates */}
          <Box
            p={4}
            borderWidth="1px"
            borderRadius="lg"
            bg="yellow.50"
            borderColor="yellow.200"
          >
            <Heading size="sm" mb={2} color="yellow.700">
              Updates ({updates.length})
            </Heading>
            {renderChangeList(updates, "yellow")}
          </Box>
        </Grid>

        {/* Deletes */}
        {deletes.length > 0 && (
          <Box
            p={4}
            borderWidth="1px"
            borderRadius="lg"
            bg="red.50"
            borderColor="red.200"
          >
            <Heading size="sm" mb={2} color="red.700">
              Deletes ({deletes.length})
            </Heading>
            {renderChangeList(deletes, "red")}
          </Box>
        )}
      </VStack>
    </Box>
  )
}

export default BranchComparisonView
