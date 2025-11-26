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
import BranchPermissions from "./BranchPermissions"

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

describe("BranchPermissions", () => {
  const mockBranches = [
    buildChangeOrder({ workflow_status: "draft" }),
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

  it("shows permissions and saves updates", async () => {
    renderWithProviders(<BranchPermissions projectId="project-123" />)

    const select = await screen.findByLabelText(/co-001/i)
    fireEvent.change(select, { target: { value: "approver" } })

    const saveButton = screen.getByRole("button", { name: /save permissions/i })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(
        screen.getByText(/permissions updated successfully/i),
      ).toBeInTheDocument()
    })

    const stored = JSON.parse(
      localStorage.getItem("branch-permissions-project-123") ?? "{}",
    )
    expect(stored["co-001"]).toBe("approver")
  })

  it("requires elevated role for main branch", async () => {
    renderWithProviders(<BranchPermissions projectId="project-123" />)

    const mainSelect = await screen.findByLabelText(/main/i)
    fireEvent.change(mainSelect, { target: { value: "viewer" } })

    expect(
      screen.getByText(/main branch requires approver/i),
    ).toBeInTheDocument()
    const saveButton = screen.getByRole("button", { name: /save permissions/i })
    expect(saveButton).toBeDisabled()
  })
})
