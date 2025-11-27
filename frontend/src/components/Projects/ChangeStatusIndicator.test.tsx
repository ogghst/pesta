import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { ChangeStatusIndicator } from "./ChangeStatusIndicator"

describe("ChangeStatusIndicator", () => {
  it("renders green badge for created status", () => {
    render(<ChangeStatusIndicator changeStatus="created" />)

    const badge = screen.getByLabelText("Created in branch")
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent("Created")
  })

  it("renders yellow badge for updated status", () => {
    render(<ChangeStatusIndicator changeStatus="updated" />)

    const badge = screen.getByLabelText("Updated in branch")
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent("Updated")
  })

  it("renders red badge for deleted status", () => {
    render(<ChangeStatusIndicator changeStatus="deleted" />)

    const badge = screen.getByLabelText("Deleted in branch")
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent("Deleted")
  })

  it("renders nothing for unchanged status", () => {
    const { container } = render(
      <ChangeStatusIndicator changeStatus="unchanged" />,
    )

    expect(container.firstChild).toBeNull()
  })

  it("is accessible with aria-label", () => {
    render(<ChangeStatusIndicator changeStatus="created" />)

    const badge = screen.getByLabelText("Created in branch")
    expect(badge).toBeInTheDocument()
  })
})
