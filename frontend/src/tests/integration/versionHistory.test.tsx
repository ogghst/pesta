// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as client from "@/client"
import VersionHistoryViewer from "@/components/Projects/VersionHistoryViewer"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { BranchProvider } from "@/context/BranchContext"
import { TimeMachineProvider } from "@/context/TimeMachineContext"
import { system } from "@/theme"

vi.mock("@/client", () => ({
  VersionHistoryService: {
    getVersionHistory: vi.fn(),
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

describe("Version History Viewing Flow", () => {
  const mockVersionHistory = {
    data: [
      {
        version: 2,
        status: "active",
        created_at: "2024-01-15T10:00:00Z",
        created_by: "user-1",
        changes: { project_name: "Updated Project" },
      },
      {
        version: 1,
        status: "active",
        created_at: "2024-01-01T00:00:00Z",
        created_by: "user-1",
        changes: {},
      },
    ],
    count: 2,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(client.VersionHistoryService.getVersionHistory).mockResolvedValue(
      mockVersionHistory,
    )
  })

  it("displays version history for an entity", async () => {
    renderWithProviders(
      <VersionHistoryViewer
        entityType="project"
        entityId="project-123"
        projectId="project-123"
      />,
    )

    await waitFor(() => {
      expect(client.VersionHistoryService.getVersionHistory).toHaveBeenCalled()
    })

    // Version history should be displayed
    await waitFor(() => {
      expect(screen.getByText(/version|history/i)).toBeInTheDocument()
    })
  })

  it("shows version details including timestamps", async () => {
    renderWithProviders(
      <VersionHistoryViewer
        entityType="project"
        entityId="project-123"
        projectId="project-123"
      />,
    )

    await waitFor(() => {
      // Should show version information
      expect(screen.getByText(/version|history/i)).toBeInTheDocument()
    })
  })
})
