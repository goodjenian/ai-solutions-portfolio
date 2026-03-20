import { render, screen } from "@testing-library/react"
import Home from "../page"

describe("Home Page", () => {
  it("renders main heading", () => {
    render(<Home />)
    expect(screen.getByText("AI Real Estate Assistant")).toBeInTheDocument()
  })

  it("renders description", () => {
    render(<Home />)
    expect(screen.getByText(/Intelligent property search/i)).toBeInTheDocument()
  })

  it("renders navigation links", () => {
    render(<Home />)
    expect(screen.getByRole("link", { name: /start searching/i })).toHaveAttribute("href", "/search")
    expect(screen.getByRole("link", { name: /ask assistant/i })).toHaveAttribute("href", "/chat")
  })
})
