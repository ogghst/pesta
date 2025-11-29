// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as client from "@/client"
import AddChangeOrder from "@/components/Projects/AddChangeOrder"
import ChangeOrdersTable from "@/components/Projects/ChangeOrdersTable"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { BranchProvider } from "@/context/BranchContext"
import { TimeMachineProvider } from "@/context/TimeMachineContext"
import { system } from "@/theme"

vi.mock("@/client", () => ({
  ChangeOrdersService: {
    listChangeOrders: vi.fn(),
    createChangeOrder: vi.fn(),
    readChangeOrder: vi.fn(),
  },
  ProjectsService: {
    readProject: vi.fn(),
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
          <BranchProvider projectId="project-123">
            <TimeMachineProvider>{ui}</TimeMachineProvider>
          </BranchProvider>
        </QueryClientProvider>
      </ColorModeProvider>
    </ChakraProvider>,
  )
}

describe("Change Order Creation Flow", () => {
  const mockProject = {
    project_id: "project-123",
    project_name: "Test Project",
    customer_name: "Test Customer",
    contract_value: "100000.00",
    start_date: "2024-01-01",
    planned_completion_date: "2024-12-31",
    project_manager_id: "user-1",
    business_status: "active",
    entity_id: "project-123",
    status: "active",
    version: 1,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(client.ProjectsService.readProject).mockResolvedValue(mockProject)
    vi.mocked(client.ChangeOrdersService.listChangeOrders).mockResolvedValue([])
  })

  it("completes change order creation flow", async () => {
    const newChangeOrder = {
      change_order_id: "co-new",
      change_order_number: "CO-001",
      title: "New Change Order",
      description: "Test description",
      requesting_party: "Customer",
      effective_date: "2024-06-01",
      workflow_status: "design",
      project_id: "project-123",
      created_by_id: "user-1",
      created_at: "2024-01-15T00:00:00Z",
      entity_id: "co-new",
      status: "active",
      version: 1,
      branch: "co-001",
    }

    vi.mocked(client.ChangeOrdersService.createChangeOrder).mockResolvedValue(
      newChangeOrder,
    )

    renderWithProviders(<AddChangeOrder projectId="project-123" />)

    // Fill in form fields
    const titleInput = screen.getByLabelText(/title/i)
    fireEvent.change(titleInput, { target: { value: "New Change Order" } })

    const descriptionInput = screen.getByLabelText(/description/i)
    fireEvent.change(descriptionInput, {
      target: { value: "Test description" },
    })

    const requestingPartyInput = screen.getByLabelText(/requesting party/i)
    fireEvent.change(requestingPartyInput, { target: { value: "Customer" } })

    // Submit form
    const submitButton = screen.getByRole("button", {
      name: /create|submit|save/i,
    })
    fireEvent.click(submitButton)

    // Wait for creation to complete
    await waitFor(() => {
      expect(client.ChangeOrdersService.createChangeOrder).toHaveBeenCalled()
    })
  })

  it("shows created change order in table after creation", async () => {
    const changeOrders = [
      {
        change_order_id: "co-1",
        change_order_number: "CO-001",
        title: "Test Change Order",
        description: "Test description",
        requesting_party: "Customer",
        effective_date: "2024-06-01",
        workflow_status: "design",
        project_id: "project-123",
        created_by_id: "user-1",
        created_at: "2024-01-15T00:00:00Z",
        entity_id: "co-1",
        status: "active",
        version: 1,
        branch: "co-001",
      },
    ]

    vi.mocked(client.ChangeOrdersService.listChangeOrders).mockResolvedValue(
      changeOrders,
    )

    renderWithProviders(<ChangeOrdersTable projectId="project-123" />)

    await waitFor(() => {
      expect(screen.getByText("CO-001")).toBeInTheDocument()
      expect(screen.getByText("Test Change Order")).toBeInTheDocument()
    })
  })
})
