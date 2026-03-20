import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { MainNav } from "../main-nav"
import { usePathname } from "next/navigation"

// Mock usePathname
jest.mock("next/navigation", () => ({
  usePathname: jest.fn(),
}))

describe("MainNav", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    window.localStorage.clear()
    document.documentElement.classList.remove("dark")
  })

  it("renders navigation links", () => {
    (usePathname as jest.Mock).mockReturnValue("/")
    render(<MainNav />)

    expect(screen.getByText("Home")).toBeInTheDocument()
    expect(screen.getByText("Search")).toBeInTheDocument()
    expect(screen.getByText("Assistant")).toBeInTheDocument()
    expect(screen.getByText("Analytics")).toBeInTheDocument()
    expect(screen.getByText("Knowledge")).toBeInTheDocument()
    expect(screen.getByText("Settings")).toBeInTheDocument()
  })

  it("highlights active link", () => {
    (usePathname as jest.Mock).mockReturnValue("/search")
    render(<MainNav />)

    const searchLink = screen.getByText("Search").closest("a")
    const homeLink = screen.getByText("Home").closest("a")

    expect(searchLink).toHaveClass("text-foreground")
    expect(homeLink).toHaveClass("text-muted-foreground")
  })

  it("toggles theme and persists selection", async () => {
    ;(usePathname as jest.Mock).mockReturnValue("/")
    render(<MainNav />)

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Toggle theme" })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole("button", { name: "Toggle theme" }))

    await waitFor(() => {
      expect(document.documentElement).toHaveClass("dark")
    })
    expect(window.localStorage.getItem("theme")).toBe("dark")

    fireEvent.click(screen.getByRole("button", { name: "Toggle theme" }))
    await waitFor(() => {
      expect(document.documentElement).not.toHaveClass("dark")
    })
    expect(window.localStorage.getItem("theme")).toBe("light")
  })
})
