/**
 * Tests for BaselineProjectSnapshot component
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { BaselineLogsService } from "@/client"
import BaselineProjectSnapshot from "../BaselineProjectSnapshot"

// Mock the client
vi.mock("@/client", () => ({
  BaselineLogsService: {
    getBaselineProjectSnapshot: vi.fn(),
  },
}))

// Mock time machine context
vi.mock("@/context/TimeMachineContext", () => ({
  useTimeMachine: () => ({
    controlDate: "2024-06-15",
  }),
}))

describe("BaselineProjectSnapshot", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  const renderComponent = (projectId: string, baselineId: string) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BaselineProjectSnapshot
          projectId={projectId}
          baselineId={baselineId}
        />
      </QueryClientProvider>,
    )
  }

  it("should render loading state initially", () => {
    vi.mocked(
      BaselineLogsService.getBaselineProjectSnapshot,
    ).mockImplementation(
      () => new Promise(() => {}), // Never resolves
    )

    renderComponent("project-1", "baseline-1")

    // Should show skeleton loading state
    expect(screen.getByText(/project baseline snapshot/i)).toBeInTheDocument()
  })

  it("should display project baseline snapshot metrics", async () => {
    const mockSnapshot = {
      baseline_project_id: "snapshot-1",
      baseline_id: "baseline-1",
      project_id: "project-1",
      planned_value: "100000.00",
      earned_value: "80000.00",
      actual_cost: "90000.00",
      budget_bac: "150000.00",
      eac: "160000.00",
      forecasted_quality: "0.9500",
      cpi: "0.8889",
      spi: "0.8000",
      tcpi: "1.1667",
      cost_variance: "-10000.00",
      schedule_variance: "-20000.00",
      created_at: "2024-06-15T00:00:00Z",
      entity_id: "entity-1",
      status: "active",
      version: 1,
    }

    vi.mocked(BaselineLogsService.getBaselineProjectSnapshot).mockResolvedValue(
      mockSnapshot as any,
    )

    renderComponent("project-1", "baseline-1")

    await waitFor(() => {
      expect(screen.getByText(/planned value/i)).toBeInTheDocument()
      expect(screen.getByText(/earned value/i)).toBeInTheDocument()
      expect(screen.getByText(/actual cost/i)).toBeInTheDocument()
      expect(screen.getByText(/budget bac/i)).toBeInTheDocument()
      expect(screen.getByText(/eac/i)).toBeInTheDocument()
    })
  })

  it("should display EVM performance indices", async () => {
    const mockSnapshot = {
      baseline_project_id: "snapshot-1",
      baseline_id: "baseline-1",
      project_id: "project-1",
      planned_value: "100000.00",
      earned_value: "80000.00",
      actual_cost: "90000.00",
      budget_bac: "150000.00",
      eac: "160000.00",
      forecasted_quality: "0.9500",
      cpi: "0.8889",
      spi: "0.8000",
      tcpi: "1.1667",
      cost_variance: "-10000.00",
      schedule_variance: "-20000.00",
      created_at: "2024-06-15T00:00:00Z",
      entity_id: "entity-1",
      status: "active",
      version: 1,
    }

    vi.mocked(BaselineLogsService.getBaselineProjectSnapshot).mockResolvedValue(
      mockSnapshot as any,
    )

    renderComponent("project-1", "baseline-1")

    await waitFor(() => {
      expect(screen.getByText(/cost performance index/i)).toBeInTheDocument()
      expect(
        screen.getByText(/schedule performance index/i),
      ).toBeInTheDocument()
      expect(
        screen.getByText(/to-complete performance index/i),
      ).toBeInTheDocument()
    })
  })

  it("should handle error state", async () => {
    vi.mocked(BaselineLogsService.getBaselineProjectSnapshot).mockRejectedValue(
      new Error("Failed to fetch"),
    )

    renderComponent("project-1", "baseline-1")

    await waitFor(() => {
      expect(
        screen.getByText(/error loading baseline snapshot/i),
      ).toBeInTheDocument()
    })
  })

  it("should handle null/undefined metrics gracefully", async () => {
    const mockSnapshot = {
      baseline_project_id: "snapshot-1",
      baseline_id: "baseline-1",
      project_id: "project-1",
      planned_value: "100000.00",
      earned_value: "80000.00",
      actual_cost: "90000.00",
      budget_bac: "150000.00",
      eac: "160000.00",
      forecasted_quality: "0.9500",
      cpi: null,
      spi: null,
      tcpi: null,
      cost_variance: "-10000.00",
      schedule_variance: "-20000.00",
      created_at: "2024-06-15T00:00:00Z",
      entity_id: "entity-1",
      status: "active",
      version: 1,
    }

    vi.mocked(BaselineLogsService.getBaselineProjectSnapshot).mockResolvedValue(
      mockSnapshot as any,
    )

    renderComponent("project-1", "baseline-1")

    await waitFor(() => {
      // Should still render without crashing
      expect(screen.getByText(/planned value/i)).toBeInTheDocument()
    })
  })
})
