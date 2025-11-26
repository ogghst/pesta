// @vitest-environment jsdom
import { ChakraProvider } from "@chakra-ui/react"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { system } from "@/theme"
import BranchTemplates from "./BranchTemplates"

describe("BranchTemplates", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  const renderWithChakra = (ui: React.ReactElement) =>
    render(
      <ChakraProvider value={system}>
        <ColorModeProvider defaultTheme="light">{ui}</ColorModeProvider>
      </ChakraProvider>,
    )

  it("creates a new template", async () => {
    renderWithChakra(<BranchTemplates projectId="project-123" />)

    fireEvent.change(screen.getByLabelText(/template name/i), {
      target: { value: "Hotfix" },
    })
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: "Quick patch template" },
    })
    fireEvent.change(screen.getByLabelText(/branch prefix/i), {
      target: { value: "hotfix-" },
    })

    fireEvent.click(screen.getByRole("button", { name: /add template/i }))

    await waitFor(() => {
      expect(screen.getByText(/^Hotfix$/i)).toBeInTheDocument()
    })

    const stored = JSON.parse(
      localStorage.getItem("branch-templates-project-123") ?? "[]",
    )
    expect(stored).toHaveLength(1)
    expect(stored[0].name).toBe("Hotfix")
  })

  it("validates template name input", () => {
    renderWithChakra(<BranchTemplates projectId="project-123" />)

    fireEvent.change(screen.getByLabelText(/template name/i), {
      target: { value: "!!" },
    })
    fireEvent.blur(screen.getByLabelText(/template name/i))

    expect(screen.getByText(/letters and numbers only/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /add template/i })).toBeDisabled()
  })

  it("applies template via callback", async () => {
    localStorage.setItem(
      "branch-templates-project-123",
      JSON.stringify([
        {
          id: "1",
          name: "Feature",
          description: "Standard feature branch",
          branchPrefix: "feat-",
        },
      ]),
    )
    const onApply = vi.fn()

    renderWithChakra(
      <BranchTemplates projectId="project-123" onApplyTemplate={onApply} />,
    )

    const applyButton = await screen.findByRole("button", {
      name: /apply feature/i,
    })
    fireEvent.click(applyButton)

    expect(onApply).toHaveBeenCalledWith({
      id: "1",
      name: "Feature",
      description: "Standard feature branch",
      branchPrefix: "feat-",
    })
  })
})
