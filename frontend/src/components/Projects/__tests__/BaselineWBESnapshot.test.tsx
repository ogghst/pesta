/**
 * Tests for BaselineWBESnapshot component
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { BaselineLogsService } from "@/client"
import BaselineWBESnapshot from "../BaselineWBESnapshot"

// Mock the client
vi.mock("@/client", () => ({
  BaselineLogsService: {
    getBaselineWbeSnapshotDetail: vi.fn(),
  },
}))

// Mock time machine context
vi.mock("@/context/TimeMachineContext", () => ({
  useTimeMachine: () => ({
    controlDate: "2024-06-15",
  }),
}))

describe("BaselineWBESnapshot", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  const renderComponent = (
    projectId: string,
    baselineId: string,
    wbeId: string,
  ) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BaselineWBESnapshot
          projectId={projectId}
          baselineId={baselineId}
          wbeId={wbeId}
        />
      </QueryClientProvider>,
    )
  }

  it("should render loading state initially", () => {
    vi.mocked(
      BaselineLogsService.getBaselineWbeSnapshotDetail,
    ).mockImplementation(() => new Promise(() => {})) // Never resolves

    renderComponent("project-1", "baseline-1", "wbe-1")

    expect(screen.getByText(/wbe baseline snapshot/i)).toBeInTheDocument()
  })

  it("should display WBE baseline snapshot metrics", async () => {
    const mockSnapshot = {
      baseline_wbe_id: "snapshot-1",
      baseline_id: "baseline-1",
      wbe_id: "wbe-1",
      planned_value: "50000.00",
      earned_value: "40000.00",
      actual_cost: "45000.00",
      budget_bac: "75000.00",
      eac: "80000.00",
      forecasted_quality: "0.9500",
      cpi: "0.8889",
      spi: "0.8000",
      tcpi: "1.1667",
      cost_variance: "-5000.00",
      schedule_variance: "-10000.00",
      created_at: "2024-06-15T00:00:00Z",
      entity_id: "entity-1",
      status: "active",
      version: 1,
    }

    vi.mocked(
      BaselineLogsService.getBaselineWbeSnapshotDetail,
    ).mockResolvedValue(mockSnapshot as any)

    renderComponent("project-1", "baseline-1", "wbe-1")

    await waitFor(() => {
      expect(screen.getByText(/planned value/i)).toBeInTheDocument()
      expect(screen.getByText(/earned value/i)).toBeInTheDocument()
      expect(screen.getByText(/actual cost/i)).toBeInTheDocument()
    })
  })

  it("should handle error state", async () => {
    vi.mocked(
      BaselineLogsService.getBaselineWbeSnapshotDetail,
    ).mockRejectedValue(new Error("Failed to fetch"))

    renderComponent("project-1", "baseline-1", "wbe-1")

    await waitFor(() => {
      expect(
        screen.getByText(/error loading baseline snapshot/i),
      ).toBeInTheDocument()
    })
  })
})
