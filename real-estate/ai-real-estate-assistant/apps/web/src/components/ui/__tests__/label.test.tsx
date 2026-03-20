import { render, screen } from "@testing-library/react"
import { Label } from "../label"

describe("Label", () => {
  it("renders correctly", () => {
    render(<Label htmlFor="test-input">Test Label</Label>)
    expect(screen.getByText("Test Label")).toBeInTheDocument()
    expect(screen.getByText("Test Label")).toHaveAttribute("for", "test-input")
  })

  it("applies custom className", () => {
    render(<Label className="custom-class">Custom Label</Label>)
    expect(screen.getByText("Custom Label")).toHaveClass("custom-class")
  })
})
