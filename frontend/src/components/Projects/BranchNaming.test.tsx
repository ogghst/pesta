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
import BranchNaming from "./BranchNaming"

vi.mock("@/client", () => ({
  ChangeOrdersService: {
    listChangeOrders: vi.fn(),
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
  title: "Change Order",
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

describe("BranchNaming", () => {
  const mockBranches = [
    buildChangeOrder({
      workflow_status: "draft",
    }),
    buildChangeOrder({
      change_order_id: "co-2",
      change_order_number: "CO-002",
      title: "Change Order 2",
      branch: "co-002",
      entity_id: "co-2",
      created_at: "2025-01-05T00:00:00Z",
    }),
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    vi.mocked(client.ChangeOrdersService.listChangeOrders).mockResolvedValue(
      mockBranches,
    )
  })

  it("allows setting custom branch names", async () => {
    renderWithProviders(<BranchNaming projectId="project-123" />)

    const input = await screen.findByLabelText(/display name for co-001/i)
    fireEvent.change(input, { target: { value: "Design Update" } })

    const saveButton = screen.getByRole("button", { name: /save names/i })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/names saved successfully/i)).toBeInTheDocument()
    })

    const stored = JSON.parse(
      localStorage.getItem("branch-names-project-123") ?? "{}",
    )
    expect(stored["co-001"]).toBe("Design Update")
  })

  it("validates branch name format", async () => {
    renderWithProviders(<BranchNaming projectId="project-123" />)

    const input = await screen.findByLabelText(/display name for co-001/i)
    fireEvent.change(input, { target: { value: "!!!" } })

    await waitFor(() => {
      expect(screen.getByText(/letters, numbers, spaces/i)).toBeInTheDocument()
    })

    const saveButton = screen.getByRole("button", { name: /save names/i })
    expect(saveButton).toBeDisabled()
  })

  it("prevents duplicate branch names", async () => {
    renderWithProviders(<BranchNaming projectId="project-123" />)

    const firstInput = await screen.findByLabelText(/display name for co-001/i)
    fireEvent.change(firstInput, { target: { value: "Feature" } })

    const secondInput = await screen.findByLabelText(/display name for co-002/i)
    fireEvent.change(secondInput, { target: { value: "Feature" } })

    await waitFor(() => {
      expect(screen.getByText(/must be unique/i)).toBeInTheDocument()
    })

    const saveButton = screen.getByRole("button", { name: /save names/i })
    expect(saveButton).toBeDisabled()
  })
})
