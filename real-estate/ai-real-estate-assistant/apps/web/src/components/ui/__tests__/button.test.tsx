import { render, screen } from "@testing-library/react"
import { Button } from "../button"

describe("Button", () => {
  it("renders correctly", () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument()
  })

  it("applies variant classes", () => {
    render(<Button variant="destructive">Destructive</Button>)
    const button = screen.getByRole("button", { name: /destructive/i })
    expect(button).toHaveClass("bg-destructive")
  })

  it("applies size classes", () => {
    render(<Button size="lg">Large</Button>)
    const button = screen.getByRole("button", { name: /large/i })
    expect(button).toHaveClass("h-11")
  })

  it("renders as child when asChild is true", () => {
    // Note: In a real test we might test the Slot behavior more deeply,
    // but here we just ensure it renders without crashing.
    // Testing Slot implementation is technically testing the library, not our code.
    // However, we can check if it merges props correctly.
    render(
      <Button asChild>
        <a href="/test">Link Button</a>
      </Button>
    )
    const link = screen.getByRole("link", { name: /link button/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute("href", "/test")
    expect(link).toHaveClass("inline-flex") // from buttonVariants
  })
})
