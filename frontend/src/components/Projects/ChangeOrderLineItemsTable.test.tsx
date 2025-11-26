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
import ChangeOrderLineItemsTable from "./ChangeOrderLineItemsTable"

vi.mock("@/client", () => ({
  ChangeOrderLineItemsService: {
    listChangeOrderLineItems: vi.fn(),
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

describe("ChangeOrderLineItemsTable", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(
      client.ChangeOrderLineItemsService.listChangeOrderLineItems,
    ).mockResolvedValue([
      {
        operation_type: "create",
        target_type: "wbe",
        branch_target_id: "wbe-1",
        main_target_id: null,
        budget_change: "1000.00",
        revenue_change: "1200.00",
        description: "Test line item",
      },
    ])
  })

  it("renders line items table", async () => {
    renderWithProviders(
      <ChangeOrderLineItemsTable
        projectId="test-project-id"
        changeOrderId="co-1"
      />,
    )

    await waitFor(() => {
      expect(
        screen.getByText(/line items|operation|budget|revenue/i),
      ).toBeInTheDocument()
    })
  })

  it("shows all line item fields", async () => {
    renderWithProviders(
      <ChangeOrderLineItemsTable
        projectId="test-project-id"
        changeOrderId="co-1"
      />,
    )

    await waitFor(() => {
      expect(screen.getByText(/create|update|delete/i)).toBeInTheDocument()
    })
  })

  it("displays operation types correctly", async () => {
    renderWithProviders(
      <ChangeOrderLineItemsTable
        projectId="test-project-id"
        changeOrderId="co-1"
      />,
    )

    await waitFor(() => {
      expect(screen.getByText("create")).toBeInTheDocument()
    })
  })

  it("shows financial impacts", async () => {
    renderWithProviders(
      <ChangeOrderLineItemsTable
        projectId="test-project-id"
        changeOrderId="co-1"
      />,
    )

    await waitFor(() => {
      expect(screen.getAllByText(/€1,000.00/).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/€1,200.00/).length).toBeGreaterThan(0)
    })
  })
})
