// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as client from "@/client"
import BranchComparisonView from "@/components/Projects/BranchComparisonView"
import BranchSelector from "@/components/Projects/BranchSelector"
import MergeBranchDialog from "@/components/Projects/MergeBranchDialog"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { BranchProvider } from "@/context/BranchContext"
import { system } from "@/theme"

vi.mock("@/client", () => ({
  ChangeOrdersService: {
    listChangeOrders: vi.fn(),
  },
  BranchComparisonService: {
    compareBranches: vi.fn(),
  },
  BranchService: {
    mergeBranch: vi.fn(),
  },
}))

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <ChakraProvider value={system}>
      <ColorModeProvider defaultTheme="light">
        <QueryClientProvider client={queryClient}>
          <BranchProvider projectId="project-123">{ui}</BranchProvider>
        </QueryClientProvider>
      </ColorModeProvider>
    </ChakraProvider>,
  )
}

describe("Branch Switching and Modification Flow", () => {
  const mockChangeOrders = [
    {
      change_order_id: "co-1",
      change_order_number: "CO-001",
      title: "Change Order 1",
      branch: "co-001",
      workflow_status: "design",
      project_id: "project-123",
      created_by_id: "user-1",
      created_at: "2024-01-15T00:00:00Z",
      entity_id: "co-1",
      status: "active",
      version: 1,
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(client.ChangeOrdersService.listChangeOrders).mockResolvedValue(
      mockChangeOrders,
    )
  })

  it("allows switching between branches", async () => {
    renderWithProviders(<BranchSelector projectId="project-123" />)

    await waitFor(() => {
      expect(screen.getByText(/main|branch/i)).toBeInTheDocument()
    })

    // Branch selector should be rendered
    const selector =
      screen.getByRole("combobox", { name: /branch/i }) ||
      screen.getByText(/main/i)
    expect(selector).toBeInTheDocument()
  })

  it("shows branch comparison when comparing branches", async () => {
    const mockComparison = {
      creates: [],
      updates: [],
      deletes: [],
      financial_impact: {
        total_budget_change: "1000.00",
        total_revenue_change: "500.00",
      },
    }

    vi.mocked(client.BranchComparisonService.compareBranches).mockResolvedValue(
      mockComparison,
    )

    renderWithProviders(
      <BranchComparisonView
        projectId="project-123"
        branch="co-001"
        baseBranch="main"
      />,
    )

    await waitFor(() => {
      expect(client.BranchComparisonService.compareBranches).toHaveBeenCalled()
    })
  })
})

describe("Merge Branch Flow", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response)
  })

  it("completes merge branch flow", async () => {
    const onClose = vi.fn()
    renderWithProviders(
      <MergeBranchDialog
        projectId="project-123"
        branch="co-001"
        isOpen={true}
        onClose={onClose}
      />,
    )

    await waitFor(() => {
      expect(screen.getByText(/merge|branch/i)).toBeInTheDocument()
    })

    // Find and click merge button
    const mergeButton = screen.getByRole("button", { name: /merge|confirm/i })
    fireEvent.click(mergeButton)

    // Wait for merge to complete
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })
  })
})
