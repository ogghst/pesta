// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen } from "@testing-library/react"
import type React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as client from "@/client"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { BranchProvider } from "@/context/BranchContext"
import { system } from "@/theme"
import BranchMergePreview from "./BranchMergePreview"

vi.mock("@/client", () => ({
  BranchComparisonService: {
    compareBranches: vi.fn(),
  },
}))

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(
    <ChakraProvider value={system}>
      <ColorModeProvider defaultTheme="light">
        <QueryClientProvider client={qc}>
          <BranchProvider projectId="test-project-id">{ui}</BranchProvider>
        </QueryClientProvider>
      </ColorModeProvider>
    </ChakraProvider>,
  )
}

describe("BranchMergePreview", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(client.BranchComparisonService.compareBranches).mockResolvedValue(
      {
        project_id: "test-project-id",
        branch: "co-001",
        base_branch: "main",
        summary: {
          creates_count: 1,
          updates_count: 1,
          deletes_count: 0,
          total_budget_change: 20000,
          total_revenue_change: 15000,
        },
        creates: [
          {
            type: "wbe",
            entity_id: "wbe-1",
            description: "Create WBE",
            revenue_change: 10000,
          },
        ],
        updates: [
          {
            type: "cost_element",
            entity_id: "ce-1",
            description: "Update Cost Element",
            budget_change: 2000,
          },
        ],
        deletes: [],
        conflicts: [
          {
            entity_id: "wbe-1",
            entity_type: "WBE",
            field: "budget_bac",
            branch_value: "120000",
            base_value: "100000",
          },
        ],
      },
    )
  })

  it("shows merge preview summary", async () => {
    renderWithProviders(
      <BranchMergePreview
        projectId="test-project-id"
        branch="co-001"
        onProceed={vi.fn()}
      />,
    )

    expect(await screen.findByText(/merge preview/i)).toBeInTheDocument()
    expect(await screen.findByText(/changes ready/i)).toBeInTheDocument()
    expect(await screen.findByText(/financial impact/i)).toBeInTheDocument()
    expect(screen.getByText(/€20,000\.00/i)).toBeInTheDocument()
    expect(screen.getByText(/€15,000\.00/i)).toBeInTheDocument()
  })

  it("displays conflicts and allows proceeding", async () => {
    const onProceed = vi.fn()
    renderWithProviders(
      <BranchMergePreview
        projectId="test-project-id"
        branch="co-001"
        onProceed={onProceed}
      />,
    )

    expect(await screen.findByText(/Branch: 120000/i)).toBeInTheDocument()

    const proceedButton = screen.getByRole("button", { name: /proceed/i })
    fireEvent.click(proceedButton)
    expect(onProceed).toHaveBeenCalled()
  })
})
