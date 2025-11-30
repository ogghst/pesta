import { Box, Container, Flex, Heading, Tabs, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { FiChevronRight } from "react-icons/fi"
import { z } from "zod"
import { BaselineLogsService, ProjectsService, WbesService } from "@/client"
import AIChat from "@/components/Projects/AIChat"
import BaselineCostElementsTable from "@/components/Projects/BaselineCostElementsTable"
import BaselineWBESnapshot from "@/components/Projects/BaselineWBESnapshot"
import { useColorModeValue } from "@/components/ui/color-mode"
import { useTimeMachine } from "@/context/TimeMachineContext"

const WBE_BASELINE_TAB_OPTIONS = [
  "info",
  "metrics",
  "cost-elements",
  "ai-assessment",
] as const

type WbeBaselineDetailTab = (typeof WBE_BASELINE_TAB_OPTIONS)[number]

const wbeBaselineDetailSearchSchema = z.object({
  tab: z.enum(WBE_BASELINE_TAB_OPTIONS).catch("metrics"),
})

export const Route = createFileRoute(
  "/_layout/projects/$id/baselines/$baselineId/wbes/$wbeId",
)({
  component: WbeBaselineDetail,
  validateSearch: (search) => wbeBaselineDetailSearchSchema.parse(search),
})

function getProjectQueryOptions({
  id,
  controlDate,
}: {
  id: string
  controlDate: string
}) {
  return {
    queryFn: () => ProjectsService.readProject({ id }),
    queryKey: ["projects", id, controlDate],
  }
}

function getBaselineQueryOptions({
  projectId,
  baselineId,
  controlDate,
}: {
  projectId: string
  baselineId: string
  controlDate: string
}) {
  return {
    queryFn: () =>
      BaselineLogsService.readBaselineLog({
        projectId,
        baselineId,
      }),
    queryKey: ["baseline-logs", projectId, baselineId, controlDate],
  }
}

function getWBEQueryOptions({
  id,
  controlDate,
}: {
  id: string
  controlDate: string
}) {
  return {
    queryFn: () => WbesService.readWbe({ id }),
    queryKey: ["wbes", id, controlDate],
  }
}

function WbeBaselineDetail() {
  const { id: projectId, baselineId, wbeId } = Route.useParams()
  const { tab } = Route.useSearch()
  const navigate = useNavigate({ from: Route.fullPath })
  const { controlDate } = useTimeMachine()
  const mutedText = useColorModeValue("fg.muted", "fg.muted")

  const handleTabChange = (value: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        tab: value as WbeBaselineDetailTab,
      }),
    })
  }

  // Fetch project data
  const { data: project, isLoading: isLoadingProject } = useQuery(
    getProjectQueryOptions({ id: projectId, controlDate }),
  )

  // Fetch baseline data
  const { data: baseline, isLoading: isLoadingBaseline } = useQuery(
    getBaselineQueryOptions({
      projectId,
      baselineId,
      controlDate,
    }),
  )

  // Fetch WBE data
  const { data: wbe, isLoading: isLoadingWbe } = useQuery(
    getWBEQueryOptions({ id: wbeId, controlDate }),
  )

  if (isLoadingProject || isLoadingBaseline || isLoadingWbe) {
    return (
      <Container maxW="container.xl" py={8}>
        <Text>Loading...</Text>
      </Container>
    )
  }

  if (!project) {
    return (
      <Container maxW="container.xl" py={8}>
        <Text>Project not found</Text>
      </Container>
    )
  }

  if (!baseline) {
    return (
      <Container maxW="container.xl" py={8}>
        <Text>Baseline not found</Text>
      </Container>
    )
  }

  if (!wbe) {
    return (
      <Container maxW="container.xl" py={8}>
        <Text>WBE not found</Text>
      </Container>
    )
  }

  // Get baseline display name
  const baselineDisplayName =
    baseline.description ||
    `${baseline.baseline_type} - ${baseline.baseline_date}`

  return (
    <Container maxW="full" py={8}>
      {/* Breadcrumb Navigation */}
      <Flex alignItems="center" gap={2} mb={4} flexWrap="wrap">
        <Link to="/projects" search={{ page: 1 }}>
          <Text
            fontSize="sm"
            color="blue.500"
            _hover={{ textDecoration: "underline" }}
          >
            Projects
          </Text>
        </Link>
        <FiChevronRight />
        <Link
          to="/projects/$id"
          params={{ id: project.project_id }}
          search={{ page: 1, tab: "baselines" } as any}
        >
          <Text
            fontSize="sm"
            color="blue.500"
            _hover={{ textDecoration: "underline" }}
          >
            {project.project_name}
          </Text>
        </Link>
        <FiChevronRight />
        <Link
          to="/projects/$id/baselines/$baselineId"
          params={{ id: project.project_id, baselineId: baseline.baseline_id }}
          search={{ baselineTab: "by-wbe" } as any}
        >
          <Text
            fontSize="sm"
            color="blue.500"
            _hover={{ textDecoration: "underline" }}
          >
            {baselineDisplayName}
          </Text>
        </Link>
        <FiChevronRight />
        <Text fontSize="sm" color="gray.600">
          {wbe.machine_type}
        </Text>
      </Flex>

      <Heading size="lg" mb={2}>
        WBE Baseline: {wbe.machine_type}
      </Heading>
      {wbe.serial_number && (
        <Text fontSize="sm" color={mutedText} mb={4}>
          Serial: {wbe.serial_number}
        </Text>
      )}

      {/* Tabbed Content */}
      <Tabs.Root
        value={tab}
        onValueChange={({ value }) => handleTabChange(value || "metrics")}
        variant="subtle"
        mt={4}
      >
        <Tabs.List>
          <Tabs.Trigger value="info">WBE Information</Tabs.Trigger>
          <Tabs.Trigger value="metrics">Metrics</Tabs.Trigger>
          <Tabs.Trigger value="cost-elements">Cost Elements</Tabs.Trigger>
          <Tabs.Trigger value="ai-assessment">AI Assessment</Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="info">
          <Box mt={4}>
            <Text color="fg.muted">
              WBE information content will be added here.
            </Text>
          </Box>
        </Tabs.Content>

        <Tabs.Content value="metrics">
          <Box mt={4}>
            <BaselineWBESnapshot
              projectId={projectId}
              baselineId={baselineId}
              wbeId={wbeId}
            />
          </Box>
        </Tabs.Content>

        <Tabs.Content value="cost-elements">
          <Box mt={4}>
            <BaselineCostElementsTable
              projectId={projectId}
              baselineId={baselineId}
            />
          </Box>
        </Tabs.Content>

        <Tabs.Content value="ai-assessment">
          <Box mt={4} h="calc(100vh - 400px)" minH="400px">
            <AIChat contextType="baseline" contextId={baselineId} />
          </Box>
        </Tabs.Content>
      </Tabs.Root>
    </Container>
  )
}
