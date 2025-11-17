import { Container } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import CostPerformanceReport from "@/components/Reports/CostPerformanceReport"

export const Route = createFileRoute(
  "/_layout/projects/$id/reports/cost-performance",
)({
  component: CostPerformanceReportPage,
})

function CostPerformanceReportPage() {
  const { id: projectId } = Route.useParams()

  return (
    <Container maxW="full" py={8}>
      <CostPerformanceReport projectId={projectId} />
    </Container>
  )
}
