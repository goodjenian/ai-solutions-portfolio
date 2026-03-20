import React from "react";
import { render, screen } from "@testing-library/react";
import AnalyticsPage from "../page";

// Mock the child component to isolate page testing
jest.mock("@/components/analytics/mortgage-calculator", () => ({
  MortgageCalculator: () => <div data-testid="mortgage-calculator">Mortgage Calculator Component</div>,
}));

describe("AnalyticsPage", () => {
  it("renders the page title", () => {
    render(<AnalyticsPage />);
    expect(screen.getByText("Analytics & Tools")).toBeInTheDocument();
  });

  it("renders the mortgage calculator section", () => {
    render(<AnalyticsPage />);
    expect(screen.getByText("Mortgage Calculator")).toBeInTheDocument();
    expect(screen.getByTestId("mortgage-calculator")).toBeInTheDocument();
  });
});
