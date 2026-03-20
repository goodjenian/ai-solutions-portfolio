import { render, screen } from "@testing-library/react"
import { Input } from "../input"

describe("Input", () => {
  it("renders correctly", () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument()
  })

  it("passes props correctly", () => {
    render(<Input type="email" required />)
    const input = screen.getByRole("textbox")
    expect(input).toHaveAttribute("type", "email")
    expect(input).toBeRequired()
  })

  it("applies custom className", () => {
    render(<Input className="custom-class" />)
    const input = screen.getByRole("textbox")
    expect(input).toHaveClass("custom-class")
  })
})
