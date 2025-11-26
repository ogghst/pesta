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
import CloneBranch from "./CloneBranch"

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

describe("CloneBranch", () => {
  const mockBranches = [buildChangeOrder()]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(client.ChangeOrdersService.listChangeOrders).mockResolvedValue(
      mockBranches,
    )
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ branch: "co-001-clone" }),
    } as Response)
  })

  it("shows available branches to clone", async () => {
    renderWithProviders(<CloneBranch projectId="project-123" />)

    await screen.findByRole("option", { name: /co-001/i })
    const select = await screen.findByLabelText(/select branch to clone/i)
    expect(select).toBeInTheDocument()
  })

  it("clones a branch successfully", async () => {
    renderWithProviders(<CloneBranch projectId="project-123" />)

    await screen.findByRole("option", { name: /co-001/i })
    const nameInput = await screen.findByLabelText(/new branch name/i)
    fireEvent.change(nameInput, { target: { value: "co-001-clone" } })

    const submitButton = screen.getByRole("button", { name: /clone branch/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(
        screen.getByText(/branch cloned to co-001-clone/i),
      ).toBeInTheDocument()
    })
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/projects/project-123/branches/co-001/clone",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_branch: "co-001-clone" }),
      }),
    )
  })

  it("requires unique branch name", async () => {
    renderWithProviders(<CloneBranch projectId="project-123" />)

    await screen.findByRole("option", { name: /co-001/i })
    const nameInput = await screen.findByLabelText(/new branch name/i)
    fireEvent.change(nameInput, { target: { value: "co-001" } })

    expect(
      await screen.findByText(/branch name already exists/i),
    ).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /clone branch/i })).toBeDisabled()
  })
})
