import {
  Alert,
  Box,
  Button,
  Flex,
  Heading,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { BranchComparisonService } from "@/client"
import type { BranchComparisonResponse } from "@/types/branchComparison"
import { formatCurrency } from "./changeOrderColumns"

interface BranchMergePreviewProps {
  projectId: string
  branch: string
  baseBranch?: string
  onProceed?: () => void
}

const BranchMergePreview = ({
  projectId,
  branch,
  baseBranch = "main",
  onProceed,
}: BranchMergePreviewProps) => {
  const { data, isLoading, isError } = useQuery<BranchComparisonResponse>({
    queryKey: ["branch-merge-preview", projectId, branch, baseBranch],
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
        <Text>Loading merge preview…</Text>
      </Box>
    )
  }

  if (isError || !data) {
    return <ErrorState />
  }

  const creates = data.creates?.length ?? 0
  const updates = data.updates?.length ?? 0
  const deletes = data.deletes?.length ?? 0
  const conflicts = data.conflicts ?? []
  const conflictCount = conflicts.length

  const derivedSummary = data.summary ?? {
    creates_count: creates,
    updates_count: updates,
    deletes_count: deletes,
    total_budget_change: data.financial_impact
      ? Number(data.financial_impact.total_budget_change)
      : 0,
    total_revenue_change: data.financial_impact
      ? Number(data.financial_impact.total_revenue_change)
      : 0,
  }

  const totalBudgetChange = derivedSummary.total_budget_change
  const totalRevenueChange = derivedSummary.total_revenue_change

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4}>
      <VStack align="stretch" gap={6}>
        <Box>
          <Heading size="md">Merge Preview</Heading>
          <Text fontWeight="medium">Changes ready to merge</Text>
          <Text color="fg.muted">
            Review changes before merging <strong>{branch}</strong> into{" "}
            <strong>{baseBranch}</strong>.
          </Text>
        </Box>
        <SimpleGrid columns={{ base: 1, md: 4 }} gap={4}>
          {[
            { label: "Creates", value: creates, helper: "New entities ready" },
            { label: "Updates", value: updates, helper: "Modified entities" },
            { label: "Deletes", value: deletes, helper: "Removed entities" },
            {
              label: "Conflicts",
              value: conflictCount,
              helper: "Requires attention",
            },
          ].map((item) => (
            <Box key={item.label} borderWidth="1px" borderRadius="md" p={3}>
              <Text fontWeight="medium">{item.label}</Text>
              <Text fontSize="2xl" fontWeight="bold">
                {item.value}
              </Text>
              <Text fontSize="sm" color="fg.muted">
                {item.helper}
              </Text>
            </Box>
          ))}
        </SimpleGrid>

        <Box>
          <Heading size="sm" mb={2}>
            Financial Impact
          </Heading>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
            <Box borderWidth="1px" borderRadius="md" p={3}>
              <Text fontWeight="medium">Total Budget Change</Text>
              <Text fontSize="2xl" fontWeight="bold">
                {formatCurrency(totalBudgetChange.toString())}
              </Text>
              <Text fontSize="sm" color="fg.muted">
                Budget impact when merging
              </Text>
            </Box>
            <Box borderWidth="1px" borderRadius="md" p={3}>
              <Text fontWeight="medium">Total Revenue Change</Text>
              <Text fontSize="2xl" fontWeight="bold">
                {formatCurrency(totalRevenueChange.toString())}
              </Text>
              <Text fontSize="sm" color="fg.muted">
                Revenue impact when merging
              </Text>
            </Box>
          </SimpleGrid>
        </Box>

        {conflictCount > 0 ? (
          <Box>
            <Heading size="sm" mb={2}>
              Conflicts
            </Heading>
            <VStack gap={3} align="stretch">
              {conflicts.map((conflict) => (
                <Box
                  key={`${conflict.entity_id}-${conflict.field}`}
                  borderWidth="1px"
                  borderRadius="md"
                  p={3}
                >
                  <Text fontWeight="semibold">
                    {conflict.entity_type} — {conflict.field}
                  </Text>
                  <Text fontSize="sm" color="fg.muted">
                    Branch: {conflict.branch_value} • Base:{" "}
                    {conflict.base_value}
                  </Text>
                </Box>
              ))}
            </VStack>
          </Box>
        ) : (
          <Alert.Root status="success" borderRadius="md">
            <Alert.Title>All clear</Alert.Title>
            <Alert.Description>
              No conflicts detected. You can safely proceed.
            </Alert.Description>
          </Alert.Root>
        )}

        <Flex justify="flex-end">
          <Button colorPalette="blue" onClick={() => onProceed?.()}>
            Proceed with Merge
          </Button>
        </Flex>
      </VStack>
    </Box>
  )
}

export default BranchMergePreview

const ErrorState = () => (
  <Alert.Root status="error" borderRadius="md">
    <Alert.Title>Unable to load merge preview</Alert.Title>
    <Alert.Description>
      Please try again or select a different branch.
    </Alert.Description>
  </Alert.Root>
)
