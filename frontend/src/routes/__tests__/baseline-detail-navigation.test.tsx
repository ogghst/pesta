/**
 * Integration tests for baseline detail navigation
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  createMemoryHistory,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { BaselineLogsService, ProjectsService } from "@/client"
import { routeTree } from "@/routeTree.gen"

// Mock the client
vi.mock("@/client", () => ({
  BaselineLogsService: {
    readBaselineLog: vi.fn(),
    getBaselineSnapshotSummary: vi.fn(),
    getBaselineProjectSnapshot: vi.fn(),
    getBaselineWbeSnapshots: vi.fn(),
    getBaselineCostElementsByWbe: vi.fn(),
  },
  ProjectsService: {
    readProject: vi.fn(),
  },
}))

// Mock time machine context
vi.mock("@/context/TimeMachineContext", () => ({
  useTimeMachine: () => ({
    controlDate: "2024-06-15",
  }),
}))

describe("Baseline Detail Navigation", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  const createTestRouter = (initialPath: string) => {
    const history = createMemoryHistory({
      initialEntries: [initialPath],
    })

    return createRouter({
      routeTree,
      history,
    })
  }

  it("should navigate to project metrics tab", async () => {
    const mockProject = {
      project_id: "project-1",
      project_name: "Test Project",
    }

    const mockBaseline = {
      baseline_id: "baseline-1",
      baseline_type: "schedule",
      baseline_date: "2024-06-15",
      description: "Test Baseline",
    }

    vi.mocked(ProjectsService.readProject).mockResolvedValue(mockProject as any)
    vi.mocked(BaselineLogsService.readBaselineLog).mockResolvedValue(
      mockBaseline as any,
    )
    vi.mocked(BaselineLogsService.getBaselineSnapshotSummary).mockResolvedValue(
      {
        total_budget_bac: "100000.00",
        total_revenue_plan: "120000.00",
        total_planned_value: "80000.00",
        cost_element_count: 5,
      } as any,
    )
    vi.mocked(BaselineLogsService.getBaselineProjectSnapshot).mockResolvedValue(
      {
        baseline_project_id: "snapshot-1",
        planned_value: "80000.00",
        earned_value: "60000.00",
        actual_cost: "70000.00",
        budget_bac: "100000.00",
        eac: "110000.00",
        cpi: "0.8571",
        spi: "0.7500",
        tcpi: "1.2500",
        cost_variance: "-10000.00",
        schedule_variance: "-20000.00",
      } as any,
    )

    const router = createTestRouter(
      "/projects/project-1/baselines/baseline-1?baselineTab=project-metrics",
    )

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText(/project baseline snapshot/i)).toBeInTheDocument()
    })
  })

  it("should navigate to WBE metrics tab", async () => {
    const mockProject = {
      project_id: "project-1",
      project_name: "Test Project",
    }

    const mockBaseline = {
      baseline_id: "baseline-1",
      baseline_type: "schedule",
      baseline_date: "2024-06-15",
      description: "Test Baseline",
    }

    vi.mocked(ProjectsService.readProject).mockResolvedValue(mockProject as any)
    vi.mocked(BaselineLogsService.readBaselineLog).mockResolvedValue(
      mockBaseline as any,
    )
    vi.mocked(BaselineLogsService.getBaselineWbeSnapshots).mockResolvedValue([
      {
        baseline_wbe_id: "snapshot-1",
        wbe_id: "wbe-1",
        budget_bac: "50000.00",
        earned_value: "40000.00",
        actual_cost: "45000.00",
        cpi: "0.8889",
        spi: "0.8000",
      },
    ] as any)

    const router = createTestRouter(
      "/projects/project-1/baselines/baseline-1?baselineTab=wbe-metrics",
    )

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText(/wbe snapshots/i)).toBeInTheDocument()
    })
  })
})
