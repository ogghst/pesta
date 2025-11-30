/**
 * Tests for BaselineWBESnapshotsTable component
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { BaselineLogsService } from "@/client"
import BaselineWBESnapshotsTable from "../BaselineWBESnapshotsTable"

// Mock the client
vi.mock("@/client", () => ({
  BaselineLogsService: {
    getBaselineWbeSnapshots: vi.fn(),
  },
}))

// Mock time machine context
vi.mock("@/context/TimeMachineContext", () => ({
  useTimeMachine: () => ({
    controlDate: "2024-06-15",
  }),
}))

// Mock router
vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual("@tanstack/react-router")
  return {
    ...actual,
    Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  }
})

describe("BaselineWBESnapshotsTable", () => {
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
        <BaselineWBESnapshotsTable
          projectId={projectId}
          baselineId={baselineId}
        />
      </QueryClientProvider>,
    )
  }

  it("should render loading state initially", () => {
    vi.mocked(BaselineLogsService.getBaselineWbeSnapshots).mockImplementation(
      () => new Promise(() => {}), // Never resolves
    )

    renderComponent("project-1", "baseline-1")

    expect(screen.getByText(/wbe snapshots/i)).toBeInTheDocument()
  })

  it("should display WBE snapshots in table", async () => {
    const mockSnapshots = [
      {
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
      },
      {
        baseline_wbe_id: "snapshot-2",
        baseline_id: "baseline-1",
        wbe_id: "wbe-2",
        planned_value: "30000.00",
        earned_value: "25000.00",
        actual_cost: "28000.00",
        budget_bac: "50000.00",
        eac: "52000.00",
        forecasted_quality: "0.9600",
        cpi: "0.8929",
        spi: "0.8333",
        tcpi: "1.2000",
        cost_variance: "-3000.00",
        schedule_variance: "-5000.00",
        created_at: "2024-06-15T00:00:00Z",
        entity_id: "entity-2",
        status: "active",
        version: 1,
      },
    ]

    vi.mocked(BaselineLogsService.getBaselineWbeSnapshots).mockResolvedValue(
      mockSnapshots as any,
    )

    renderComponent("project-1", "baseline-1")

    await waitFor(() => {
      expect(screen.getByText(/budget bac/i)).toBeInTheDocument()
      expect(screen.getByText(/earned ev/i)).toBeInTheDocument()
      expect(screen.getByText(/actual ac/i)).toBeInTheDocument()
      expect(screen.getByText(/cpi/i)).toBeInTheDocument()
      expect(screen.getByText(/spi/i)).toBeInTheDocument()
    })
  })

  it("should display empty state when no snapshots", async () => {
    vi.mocked(BaselineLogsService.getBaselineWbeSnapshots).mockResolvedValue(
      [] as any,
    )

    renderComponent("project-1", "baseline-1")

    await waitFor(() => {
      expect(screen.getByText(/no wbe snapshots found/i)).toBeInTheDocument()
    })
  })

  it("should handle error state", async () => {
    vi.mocked(BaselineLogsService.getBaselineWbeSnapshots).mockRejectedValue(
      new Error("Failed to fetch"),
    )

    renderComponent("project-1", "baseline-1")

    // Table should still render, error handling is at query level
    await waitFor(() => {
      expect(screen.getByText(/wbe snapshots/i)).toBeInTheDocument()
    })
  })
})
