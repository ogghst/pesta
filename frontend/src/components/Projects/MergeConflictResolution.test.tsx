// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { fireEvent, render, screen } from "@testing-library/react"
import type React from "react"
import { describe, expect, it, vi } from "vitest"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { system } from "@/theme"
import MergeConflictResolution from "./MergeConflictResolution"

function renderWithChakra(ui: React.ReactElement) {
  return render(
    <ChakraProvider value={system}>
      <ColorModeProvider defaultTheme="light">{ui}</ColorModeProvider>
    </ChakraProvider>,
  )
}

describe("MergeConflictResolution", () => {
  const conflicts = [
    {
      id: "conflict-1",
      entityId: "wbe-1",
      entityType: "WBE",
      field: "budget_bac",
      branchValue: "120000",
      baseValue: "100000",
    },
  ]

  it("shows conflicts and allows selecting strategies", () => {
    const onResolve = vi.fn()
    renderWithChakra(
      <MergeConflictResolution conflicts={conflicts} onResolve={onResolve} />,
    )

    expect(screen.getByText(/budget_bac/i)).toBeInTheDocument()
    const select = screen.getByLabelText(/resolution strategy/i)
    fireEvent.change(select, { target: { value: "branch" } })

    const button = screen.getByRole("button", { name: /apply resolution/i })
    fireEvent.click(button)
    expect(onResolve).toHaveBeenCalledWith({ "conflict-1": "branch" })
  })

  it("requires custom value before applying resolution", () => {
    const onResolve = vi.fn()
    renderWithChakra(
      <MergeConflictResolution conflicts={conflicts} onResolve={onResolve} />,
    )

    const select = screen.getByLabelText(/resolution strategy/i)
    fireEvent.change(select, { target: { value: "custom" } })

    const applyButton = screen.getByRole("button", {
      name: /apply resolution/i,
    })
    expect(applyButton).toBeDisabled()

    const input = screen.getByPlaceholderText(/enter custom value/i)
    fireEvent.change(input, { target: { value: "105000" } })

    expect(applyButton).not.toBeDisabled()
    fireEvent.click(applyButton)
    expect(onResolve).toHaveBeenCalledWith({ "conflict-1": "105000" })
  })
})
