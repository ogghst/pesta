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
import RollbackVersion from "./RollbackVersion"

vi.mock("@/client", () => ({
  WbesService: {
    updateWbe: vi.fn(),
  },
  CostElementsService: {
    updateCostElement: vi.fn(),
  },
  VersionHistoryService: {
    getEntityVersionHistory: vi.fn(),
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

describe("RollbackVersion", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(
      client.VersionHistoryService.getEntityVersionHistory,
    ).mockResolvedValue({
      entity_type: "wbe",
      entity_id: "wbe-1",
      branch: "main",
      count: 1,
      versions: [
        {
          version: 1,
          status: "active",
          branch: "main",
          created_at: "2025-01-01T00:00:00Z",
        },
      ],
    } as any)
  })

  it("shows rollback confirmation", () => {
    renderWithProviders(
      <RollbackVersion
        entityType="wbe"
        entityId="wbe-1"
        targetVersion={1}
        branch="main"
        isOpen={true}
        onClose={() => {}}
      />,
    )

    expect(
      screen.getByRole("heading", { name: /Rollback to Version 1/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /Confirm Rollback/i }),
    ).toBeInTheDocument()
  })

  it("executes rollback", async () => {
    const onClose = vi.fn()
    renderWithProviders(
      <RollbackVersion
        entityType="wbe"
        entityId="wbe-1"
        targetVersion={1}
        branch="main"
        isOpen={true}
        onClose={onClose}
      />,
    )

    await screen.findByText(/Version 1 was created/i)

    const confirmButton = await screen.findByRole("button", {
      name: /confirm|rollback/i,
    })
    fireEvent.click(confirmButton)

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled()
    })
  })
})
