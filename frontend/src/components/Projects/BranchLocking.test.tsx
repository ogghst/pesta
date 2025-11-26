// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as client from "@/client"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { BranchProvider } from "@/context/BranchContext"
import { system } from "@/theme"
import BranchLocking from "./BranchLocking"

vi.mock("@/client", () => ({
  ChangeOrdersService: {
    listChangeOrders: vi.fn(),
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

const buildChangeOrder = (
  overrides: Partial<client.ChangeOrderPublic> = {},
): client.ChangeOrderPublic => ({
  change_order_id: "co-1",
  change_order_number: "CO-001",
  title: "Change Order 1",
  description: "Test change order",
  requesting_party: "Project Owner",
  effective_date: "2025-01-01",
  workflow_status: "design",
  project_id: "project-123",
  created_by_id: "user-1",
  created_at: "2025-01-01T00:00:00Z",
  entity_id: "co-1",
  status: "active",
  version: 1,
  branch: "co-001",
  ...overrides,
})

describe("BranchLocking", () => {
  const mockBranches = [buildChangeOrder()]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(client.ChangeOrdersService.listChangeOrders).mockResolvedValue(
      mockBranches,
    )
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response)
  })

  it("renders branches with initial unlocked status", async () => {
    renderWithProviders(<BranchLocking projectId="project-123" />)

    await screen.findByText(/^co-001$/i)
    expect(screen.getAllByText(/^Unlocked$/i).length).toBeGreaterThan(0)
  })

  it("locks a branch via API call", async () => {
    renderWithProviders(<BranchLocking projectId="project-123" />)

    const lockButton = await screen.findByRole("button", {
      name: /lock co-001/i,
    })
    fireEvent.click(lockButton)

    await waitFor(() => {
      expect(screen.getByText(/locked by you/i)).toBeInTheDocument()
    })
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/projects/project-123/branches/co-001/lock",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }),
    )
  })

  it("unlocks a branch", async () => {
    renderWithProviders(<BranchLocking projectId="project-123" />)

    const lockButton = await screen.findByRole("button", {
      name: /lock co-001/i,
    })
    fireEvent.click(lockButton)
    await screen.findByText(/locked by you/i)

    fireEvent.click(screen.getByRole("button", { name: /unlock co-001/i }))
    await waitFor(() => {
      expect(screen.getByText(/unlocked/i)).toBeInTheDocument()
    })
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/projects/project-123/branches/co-001/lock",
      expect.objectContaining({ method: "DELETE" }),
    )
  })
})
