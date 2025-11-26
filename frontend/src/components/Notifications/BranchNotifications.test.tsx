// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ColorModeProvider } from "@/components/ui/color-mode"
import { system } from "@/theme"
import BranchNotifications from "./BranchNotifications"

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <ChakraProvider value={system}>
      <ColorModeProvider defaultTheme="light">
        <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
      </ColorModeProvider>
    </ChakraProvider>,
  )
}

describe("BranchNotifications", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("renders notifications returned by the API", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        data: [
          {
            notification_id: "notif-1",
            branch: "co-001",
            event_type: "merge_completed",
            message: "Branch co-001 merged successfully",
            recipients: ["pm@example.com"],
            context: { change_order_id: "co-uuid" },
            created_at: "2025-01-01T00:00:00Z",
          },
        ],
        count: 1,
      }),
    } as Response)

    renderWithProviders(
      <BranchNotifications projectId="project-123" limit={5} />,
    )

    await screen.findByText(/Branch co-001 merged successfully/i)
    expect(screen.getByText(/merge\s+completed/i)).toBeInTheDocument()
    expect(screen.getByText(/pm@example.com/i)).toBeInTheDocument()
  })

  it("shows an empty state when no notifications exist", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        data: [],
        count: 0,
      }),
    } as Response)

    renderWithProviders(<BranchNotifications projectId="project-123" />)

    await waitFor(() => {
      expect(
        screen.getByText(/no branch notifications yet/i),
      ).toBeInTheDocument()
    })
  })
})
