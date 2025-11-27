// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { render, screen } from "@testing-library/react"
import type { ReactElement } from "react"
import { describe, expect, it, vi } from "vitest"
import * as BranchContext from "@/context/BranchContext"
import { system } from "@/theme"
import { ViewModeToggle } from "./ViewModeToggle"

// Mock the useBranch hook
vi.mock("@/context/BranchContext", () => ({
  useBranch: vi.fn(),
}))

describe("ViewModeToggle", () => {
  const renderWithChakra = (ui: ReactElement) =>
    render(<ChakraProvider value={system}>{ui}</ChakraProvider>)

  it("renders toggle with current view mode", () => {
    const mockSetViewMode = vi.fn()
    vi.mocked(BranchContext.useBranch).mockReturnValue({
      currentBranch: "co-001",
      viewMode: "merged",
      isLoading: false,
      setCurrentBranch: vi.fn(),
      setViewMode: mockSetViewMode,
      availableBranches: ["main", "co-001"],
    })

    renderWithChakra(<ViewModeToggle />)

    expect(screen.getByText("Merged View")).toBeInTheDocument()
    expect(screen.getByText("Branch Only")).toBeInTheDocument()
  })

  it("calls setViewMode when toggled", () => {
    const mockSetViewMode = vi.fn()
    vi.mocked(BranchContext.useBranch).mockReturnValue({
      currentBranch: "co-001",
      viewMode: "merged",
      isLoading: false,
      setCurrentBranch: vi.fn(),
      setViewMode: mockSetViewMode,
      availableBranches: ["main", "co-001"],
    })

    renderWithChakra(<ViewModeToggle />)

    const branchOnlyRadio = screen.getByLabelText("Branch Only")
    branchOnlyRadio.click()

    expect(mockSetViewMode).toHaveBeenCalledWith("branch-only")
  })

  it("hides when branch is main", () => {
    vi.mocked(BranchContext.useBranch).mockReturnValue({
      currentBranch: "main",
      viewMode: "merged",
      isLoading: false,
      setCurrentBranch: vi.fn(),
      setViewMode: vi.fn(),
      availableBranches: ["main"],
    })

    const { container } = renderWithChakra(<ViewModeToggle />)

    expect(container.firstChild).toBeNull()
  })
})
