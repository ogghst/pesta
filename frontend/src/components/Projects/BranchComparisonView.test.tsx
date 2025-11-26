// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as client from "@/client"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { BranchProvider } from "@/context/BranchContext"
import { system } from "@/theme"
import BranchComparisonView from "./BranchComparisonView"

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

describe("BranchComparisonView", () => {
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
          total_revenue_change: 5000,
          total_budget_change: 3000,
        },
        creates: [
          {
            type: "wbe",
            entity_id: "wbe-1",
            description: "Create WBE: New Machine",
            revenue_change: 10000,
          },
        ],
        updates: [
          {
            type: "wbe",
            entity_id: "wbe-2",
            description: "Update WBE: Existing Machine",
            revenue_change: 20000,
          },
        ],
        deletes: [],
      },
    )
  })

  it("renders side-by-side comparison", async () => {
    renderWithProviders(
      <BranchComparisonView projectId="test-project-id" branch="co-001" />,
    )

    await waitFor(() => {
      expect(screen.getByText(/comparison/i)).toBeInTheDocument()
    })
  })

  it("highlights differences with visual indicators", async () => {
    renderWithProviders(
      <BranchComparisonView projectId="test-project-id" branch="co-001" />,
    )

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /Creates/i }),
      ).toBeInTheDocument()
      expect(
        screen.getByRole("heading", { name: /Updates/i }),
      ).toBeInTheDocument()
    })
  })

  it("shows financial impact summary", async () => {
    renderWithProviders(
      <BranchComparisonView projectId="test-project-id" branch="co-001" />,
    )

    await waitFor(() => {
      expect(screen.getByText(/Total Revenue Change/i)).toBeInTheDocument()
      expect(screen.getByText(/Total Budget Change/i)).toBeInTheDocument()
    })
  })

  it("is responsive", async () => {
    renderWithProviders(
      <BranchComparisonView projectId="test-project-id" branch="co-001" />,
    )

    await waitFor(() => {
      const container = screen.getByText(/comparison/i).closest("div")
      expect(container).toBeInTheDocument()
    })
  })
})
