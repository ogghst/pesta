/**
 * Tests for BaselineSummary component enhancements
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { BaselineLogsService } from "@/client"
import BaselineSummary from "../BaselineSummary"

// Mock the client
vi.mock("@/client", () => ({
  BaselineLogsService: {
    getBaselineSnapshotSummary: vi.fn(),
    getBaselineProjectSnapshot: vi.fn(),
  },
}))

// Mock time machine context
vi.mock("@/context/TimeMachineContext", () => ({
  useTimeMachine: () => ({
    controlDate: "2024-06-15",
  }),
}))

describe("BaselineSummary", () => {
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
        <BaselineSummary projectId={projectId} baselineId={baselineId} />
      </QueryClientProvider>,
    )
  }

  it("should display EVM indices when project snapshot is available", async () => {
    const mockSummary = {
      total_budget_bac: "150000.00",
      total_revenue_plan: "200000.00",
      total_planned_value: "100000.00",
      total_actual_ac: "90000.00",
      total_forecast_eac: "160000.00",
      total_earned_ev: "80000.00",
      cost_element_count: 10,
    }

    const mockProjectSnapshot = {
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

    vi.mocked(BaselineLogsService.getBaselineSnapshotSummary).mockResolvedValue(
      mockSummary as any,
    )
    vi.mocked(BaselineLogsService.getBaselineProjectSnapshot).mockResolvedValue(
      mockProjectSnapshot as any,
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
      expect(screen.getByText(/cost variance/i)).toBeInTheDocument()
      expect(screen.getByText(/schedule variance/i)).toBeInTheDocument()
    })
  })

  it("should display summary metrics correctly", async () => {
    const mockSummary = {
      total_budget_bac: "150000.00",
      total_revenue_plan: "200000.00",
      total_planned_value: "100000.00",
      total_actual_ac: "90000.00",
      total_forecast_eac: "160000.00",
      total_earned_ev: "80000.00",
      cost_element_count: 10,
    }

    vi.mocked(BaselineLogsService.getBaselineSnapshotSummary).mockResolvedValue(
      mockSummary as any,
    )
    vi.mocked(BaselineLogsService.getBaselineProjectSnapshot).mockResolvedValue(
      null as any,
    )

    renderComponent("project-1", "baseline-1")

    await waitFor(() => {
      expect(screen.getByText(/total budget bac/i)).toBeInTheDocument()
      expect(screen.getByText(/total revenue plan/i)).toBeInTheDocument()
      expect(screen.getByText(/total planned value/i)).toBeInTheDocument()
    })
  })
})
