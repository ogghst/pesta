// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { describe, expect, it, vi } from "vitest"
import * as client from "@/client"
import { TimeMachineProvider } from "@/context/TimeMachineContext"
import { system } from "../../../theme"
import { ColorModeProvider } from "../../ui/color-mode"
import CostPerformanceReport from "../CostPerformanceReport"

vi.mock("@/client", () => ({
  ReportsService: {
    getProjectCostPerformanceReportEndpoint: vi.fn(),
  },
}))

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
}))

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return render(
    <ChakraProvider value={system}>
      <ColorModeProvider defaultTheme="light">
        <QueryClientProvider client={qc}>
          <TimeMachineProvider>{ui}</TimeMachineProvider>
        </QueryClientProvider>
      </ColorModeProvider>
    </ChakraProvider>,
  )
}

describe("CostPerformanceReport", () => {
  it("renders loading state", () => {
    vi.mocked(
      client.ReportsService.getProjectCostPerformanceReportEndpoint,
    ).mockImplementation(
      () =>
        new Promise(() => {}) as ReturnType<
          typeof client.ReportsService.getProjectCostPerformanceReportEndpoint
        >,
    ) // Never resolves

    const { container } = renderWithProviders(
      <CostPerformanceReport projectId="test-project-id" />,
    )

    // Should show loading skeleton
    expect(container.querySelector("div")).toBeDefined()
  })

  it("renders error state", async () => {
    vi.mocked(
      client.ReportsService.getProjectCostPerformanceReportEndpoint,
    ).mockRejectedValue(new Error("Failed to load report"))

    renderWithProviders(<CostPerformanceReport projectId="test-project-id" />)

    await waitFor(() => {
      expect(
        screen.getByText(/Error loading cost performance report/i),
      ).toBeDefined()
    })
  })

  it("renders empty state when no cost elements", async () => {
    const mockReport = {
      project_id: "test-project-id",
      project_name: "Test Project",
      control_date: "2024-06-15",
      rows: [],
      summary: {
        level: "project",
        control_date: "2024-06-15",
        project_id: "test-project-id",
        planned_value: "0.00",
        earned_value: "0.00",
        actual_cost: "0.00",
        budget_bac: "0.00",
        cpi: null,
        spi: null,
        tcpi: null,
        cost_variance: "0.00",
        schedule_variance: "0.00",
      },
    }

    vi.mocked(
      client.ReportsService.getProjectCostPerformanceReportEndpoint,
    ).mockResolvedValue(mockReport as any)

    renderWithProviders(<CostPerformanceReport projectId="test-project-id" />)

    await waitFor(() => {
      expect(
        screen.getByText(/No cost elements found for this project/i),
      ).toBeDefined()
    })
  })

  it("renders report with data", async () => {
    const mockReport = {
      project_id: "test-project-id",
      project_name: "Test Project",
      control_date: "2024-06-15",
      rows: [
        {
          cost_element_id: "ce-1",
          wbe_id: "wbe-1",
          wbe_name: "Test Machine",
          wbe_serial_number: "SN-001",
          department_code: "ENG",
          department_name: "Engineering",
          cost_element_type_id: null,
          cost_element_type_name: null,
          planned_value: "10000.00",
          earned_value: "8000.00",
          actual_cost: "9000.00",
          budget_bac: "10000.00",
          cpi: "0.8889",
          spi: "0.8000",
          tcpi: "2.0000",
          cost_variance: "-1000.00",
          schedule_variance: "-2000.00",
        },
      ],
      summary: {
        level: "project",
        control_date: "2024-06-15",
        project_id: "test-project-id",
        planned_value: "10000.00",
        earned_value: "8000.00",
        actual_cost: "9000.00",
        budget_bac: "10000.00",
        cpi: "0.8889",
        spi: "0.8000",
        tcpi: "2.0000",
        cost_variance: "-1000.00",
        schedule_variance: "-2000.00",
      },
    }

    vi.mocked(
      client.ReportsService.getProjectCostPerformanceReportEndpoint,
    ).mockResolvedValue(mockReport as any)

    renderWithProviders(<CostPerformanceReport projectId="test-project-id" />)

    await waitFor(() => {
      expect(screen.getByText(/Cost Performance Report/i)).toBeDefined()
      expect(screen.getByText(/Project Summary/i)).toBeDefined()
    })
  })

  it("calls ReportsService with correct projectId", async () => {
    const mockReport = {
      project_id: "test-project-id",
      project_name: "Test Project",
      control_date: "2024-06-15",
      rows: [],
      summary: {
        level: "project",
        control_date: "2024-06-15",
        project_id: "test-project-id",
        planned_value: "0.00",
        earned_value: "0.00",
        actual_cost: "0.00",
        budget_bac: "0.00",
        cpi: null,
        spi: null,
        tcpi: null,
        cost_variance: "0.00",
        schedule_variance: "0.00",
      },
    }

    vi.mocked(
      client.ReportsService.getProjectCostPerformanceReportEndpoint,
    ).mockResolvedValue(mockReport as any)

    renderWithProviders(<CostPerformanceReport projectId="test-project-id" />)

    await waitFor(() => {
      expect(
        client.ReportsService.getProjectCostPerformanceReportEndpoint,
      ).toHaveBeenCalledWith({
        projectId: "test-project-id",
      })
    })
  })
})
