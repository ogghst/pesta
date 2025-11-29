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
import BranchSelector from "./BranchSelector"

const mockNavigate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => mockNavigate,
}))

vi.mock("@/client", () => ({
  ChangeOrdersService: {
    listChangeOrders: vi.fn(),
  },
  OpenAPI: {
    BASE: "http://localhost:8010",
  },
}))

vi.mock("@/hooks/useCustomToast", () => ({
  __esModule: true,
  default: () => ({
    showErrorToast: vi.fn(),
    showSuccessToast: vi.fn(),
    showInfoToast: vi.fn(),
  }),
}))

// Mock global fetch for branch locks endpoint
const mockFetch = vi.fn()
global.fetch = mockFetch

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

describe("BranchSelector", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()

    // Mock localStorage
    Storage.prototype.getItem = vi.fn((key: string) => {
      if (key === "current-branch-test-project-id") return "main"
      return null
    })
    Storage.prototype.setItem = vi.fn()

    // Mock change orders with a branch
    vi.mocked(client.ChangeOrdersService.listChangeOrders).mockResolvedValue([
      {
        change_order_id: "co-1",
        change_order_number: "CO-001",
        title: "Test CO",
        description: "Test",
        requesting_party: "Test",
        effective_date: "2025-01-01",
        workflow_status: "design",
        project_id: "test-project-id",
        created_by_id: "user-1",
        created_at: "2025-01-01T00:00:00Z",
        entity_id: "co-1",
        status: "active",
        version: 1,
        branch: "co-001",
      },
    ])

    // Mock fetch for branch locks endpoint
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ locks: {} }),
    })
  })

  it("renders branch text and switch button", () => {
    renderWithProviders(<BranchSelector projectId="test-project-id" />)

    // Should show current branch text
    expect(screen.getByText(/Branch:/i)).toBeInTheDocument()
    expect(screen.getByText("main")).toBeInTheDocument()

    // Should show Switch button
    const switchButton = screen.getByRole("button", { name: /switch/i })
    expect(switchButton).toBeInTheDocument()
  })

  it("shows current branch", () => {
    renderWithProviders(<BranchSelector projectId="test-project-id" />)

    // Default branch should be 'main'
    expect(screen.getByText("main")).toBeInTheDocument()
  })

  it("opens dialog when switch button is clicked", async () => {
    renderWithProviders(<BranchSelector projectId="test-project-id" />)

    const switchButton = screen.getByRole("button", { name: /switch/i })
    fireEvent.click(switchButton)

    // Wait for dialog to open
    await waitFor(() => {
      expect(screen.getByText(/Select Branch/i)).toBeInTheDocument()
    })

    // Dialog should be visible
    expect(
      screen.getByText(/Select a branch to switch to/i),
    ).toBeInTheDocument()
  })

  it("displays branches in dialog after opening", async () => {
    renderWithProviders(<BranchSelector projectId="test-project-id" />)

    const switchButton = screen.getByRole("button", { name: /switch/i })
    fireEvent.click(switchButton)

    // Wait for dialog and branches to load
    await waitFor(() => {
      expect(screen.getByText(/Select Branch/i)).toBeInTheDocument()
    })

    await waitFor(
      () => {
        // Should show main branch and change order branch in the table
        expect(screen.getByText("main")).toBeInTheDocument()
        expect(screen.getByText("co-001")).toBeInTheDocument()
      },
      { timeout: 3000 },
    )
  })

  it("opens confirmation dialog when a branch is selected", async () => {
    renderWithProviders(<BranchSelector projectId="test-project-id" />)

    // Open the branch selection dialog
    const switchButton = screen.getByRole("button", { name: /switch/i })
    fireEvent.click(switchButton)

    await waitFor(() => {
      expect(screen.getByText(/Select Branch/i)).toBeInTheDocument()
    })

    // Wait for branches to load and find the branch row
    await waitFor(
      () => {
        expect(screen.getByText("co-001")).toBeInTheDocument()
      },
      { timeout: 3000 },
    )

    // Find all table rows and click on the one containing "co-001"
    await waitFor(() => {
      const rows = screen.getAllByRole("row")
      const branchRow = rows.find((row) => row.textContent?.includes("co-001"))
      expect(branchRow).toBeInTheDocument()
      if (branchRow) {
        fireEvent.click(branchRow)
      }
    })

    // Wait for confirmation dialog
    await waitFor(() => {
      expect(screen.getByText(/Confirm Branch Switch/i)).toBeInTheDocument()
    })

    // Should show branch names in confirmation
    expect(screen.getByText(/main/i)).toBeInTheDocument()
    expect(screen.getByText(/co-001/i)).toBeInTheDocument()
  })
})
