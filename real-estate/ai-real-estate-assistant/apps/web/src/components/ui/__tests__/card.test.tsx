import { render, screen } from "@testing-library/react"
import {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
} from "../card"

describe("Card", () => {
  it("renders all subcomponents correctly", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card Description</CardDescription>
        </CardHeader>
        <CardContent>Card Content</CardContent>
        <CardFooter>Card Footer</CardFooter>
      </Card>
    )

    expect(screen.getByText("Card Title")).toBeInTheDocument()
    expect(screen.getByText("Card Description")).toBeInTheDocument()
    expect(screen.getByText("Card Content")).toBeInTheDocument()
    expect(screen.getByText("Card Footer")).toBeInTheDocument()
  })

  it("applies custom classNames", () => {
    render(
      <Card className="card-class">
        <CardHeader className="header-class">Header</CardHeader>
        <CardContent className="content-class">Content</CardContent>
        <CardFooter className="footer-class">Footer</CardFooter>
      </Card>
    )

    // Using text content to find elements since they are divs
    expect(screen.getByText("Header")).toHaveClass("header-class")
    expect(screen.getByText("Content")).toHaveClass("content-class")
    expect(screen.getByText("Footer")).toHaveClass("footer-class")
    // Card wrapper is a bit harder to select by text, but we can verify it renders
  })
})
