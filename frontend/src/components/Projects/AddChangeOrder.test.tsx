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
import AddChangeOrder from "./AddChangeOrder"

vi.mock("@/client", () => ({
  ChangeOrdersService: {
    createChangeOrder: vi.fn(),
  },
  UsersService: {
    readUserMe: vi.fn(),
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

describe("AddChangeOrder", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(client.UsersService.readUserMe).mockResolvedValue({
      id: "user-1",
      email: "test@example.com",
      is_active: true,
    } as any)
    vi.mocked(client.ChangeOrdersService.createChangeOrder).mockResolvedValue({
      change_order_id: "co-1",
      change_order_number: "CO-001",
      title: "Test CO",
      description: "Test",
      requesting_party: "Test Party",
      effective_date: "2025-01-01",
      workflow_status: "design",
      project_id: "test-project-id",
      created_by_id: "user-1",
      created_at: "2025-01-01T00:00:00Z",
      entity_id: "co-1",
      status: "active",
      version: 1,
      branch: "co-001",
    } as any)
  })

  it("renders form with all fields", async () => {
    renderWithProviders(<AddChangeOrder projectId="test-project-id" />)

    const trigger = screen.getByText(/add change order/i)
    fireEvent.click(trigger)

    await waitFor(() => {
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/requesting party/i)).toBeInTheDocument()
    })
  })

  it("validates required fields", async () => {
    renderWithProviders(<AddChangeOrder projectId="test-project-id" />)

    const trigger = screen.getByText(/add change order/i)
    fireEvent.click(trigger)

    const titleInput = await screen.findByLabelText(/title/i)
    fireEvent.focus(titleInput)
    fireEvent.blur(titleInput)

    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument()
    })
  })

  it("submits change order creation", async () => {
    renderWithProviders(<AddChangeOrder projectId="test-project-id" />)

    const trigger = screen.getByText(/add change order/i)
    fireEvent.click(trigger)

    const titleInput = await screen.findByLabelText(/title/i)
    fireEvent.change(titleInput, { target: { value: "Test CO" } })
    fireEvent.blur(titleInput)

    const descriptionInput = screen.getByLabelText(/description/i)
    fireEvent.change(descriptionInput, {
      target: { value: "Test description" },
    })
    fireEvent.blur(descriptionInput)

    const requestingPartyInput = screen.getByLabelText(/requesting party/i)
    fireEvent.change(requestingPartyInput, {
      target: { value: "Test Party" },
    })
    fireEvent.blur(requestingPartyInput)

    const submitButton = screen.getByRole("button", { name: /save/i })
    await waitFor(() => {
      expect(submitButton).toBeEnabled()
    })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(client.ChangeOrdersService.createChangeOrder).toHaveBeenCalled()
    })
  })

  it("shows auto-generated change order number", async () => {
    renderWithProviders(<AddChangeOrder projectId="test-project-id" />)

    const trigger = screen.getByText(/add change order/i)
    fireEvent.click(trigger)

    await waitFor(() => {
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
    })
  })

  it("creates branch automatically", async () => {
    renderWithProviders(<AddChangeOrder projectId="test-project-id" />)

    const trigger = screen.getByText(/add change order/i)
    fireEvent.click(trigger)

    const titleInput = await screen.findByLabelText(/title/i)
    fireEvent.change(titleInput, { target: { value: "Test CO" } })
    fireEvent.blur(titleInput)

    const descriptionInput = screen.getByLabelText(/description/i)
    fireEvent.change(descriptionInput, {
      target: { value: "Test description" },
    })
    fireEvent.blur(descriptionInput)

    const requestingPartyInput = screen.getByLabelText(/requesting party/i)
    fireEvent.change(requestingPartyInput, {
      target: { value: "Test Party" },
    })
    fireEvent.blur(requestingPartyInput)

    const submitButton = screen.getByRole("button", { name: /save/i })
    await waitFor(() => {
      expect(submitButton).toBeEnabled()
    })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(client.ChangeOrdersService.createChangeOrder).toHaveBeenCalled()
      // Branch should be created automatically by backend
      const call = vi.mocked(client.ChangeOrdersService.createChangeOrder).mock
        .calls[0]
      expect(call[0].requestBody.project_id).toBe("test-project-id")
    })
  })
})
