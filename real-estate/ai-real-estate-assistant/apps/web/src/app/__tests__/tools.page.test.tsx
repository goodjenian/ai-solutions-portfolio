import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import ToolsPage from "../tools/page";

// Mock API functions
jest.mock("@/lib/api", () => ({
  calculateMortgage: jest.fn(async () => ({ monthly_payment: 1234.56 })),
  comparePropertiesApi: jest.fn(async () => ({
    summary: { count: 2, min_price: 100000, max_price: 150000, price_difference: 50000 },
  })),
  exportPropertiesByIds: jest.fn(async () => ({
    filename: "properties.csv",
    blob: new Blob(["a"], { type: "text/csv" }),
  })),
  priceAnalysisApi: jest.fn(async () => ({ count: 10, average_price: 200000, median_price: 195000 })),
  locationAnalysisApi: jest.fn(async () => ({
    city: "Warsaw",
    neighborhood: "Śródmieście",
    lat: 52.2297,
    lon: 21.0122,
  })),
  valuationApi: jest.fn(async () => ({ property_id: "p1", estimated_value: 250000 })),
  legalCheckApi: jest.fn(async () => ({ risks: [], score: 0 })),
  enrichAddressApi: jest.fn(async () => ({ address: "Some St 1", data: {} })),
  crmSyncContactApi: jest.fn(async () => ({ id: "contact-123" })),
  listPromptTemplates: jest.fn(async () => [
    {
      id: "buyer_followup_email_v1",
      title: "Buyer follow-up email",
      category: "email",
      description: "Follow-up email after an inquiry with next steps and a short question set.",
      template_text: "Subject: Quick follow-up on {{property_address}}",
      variables: [
        { name: "property_address", description: "Address", required: true, example: "Main St 10" },
        { name: "buyer_name", description: "Name", required: true, example: "Alex" },
        { name: "agent_name", description: "Agent", required: true, example: "Maria" },
      ],
    },
  ]),
  applyPromptTemplate: jest.fn(async () => ({
    template_id: "buyer_followup_email_v1",
    rendered_text: "Subject: Quick follow-up on Main St 10\n\nHi Alex,\n\nBest,\nMaria",
  })),
}));

describe("ToolsPage", () => {
  it("renders and calculates mortgage", async () => {
    render(<ToolsPage />);
    fireEvent.change(screen.getByPlaceholderText("Property price"), { target: { value: "300000" } });
    fireEvent.change(screen.getByPlaceholderText("Down payment %"), { target: { value: "20" } });
    fireEvent.change(screen.getByPlaceholderText("Interest rate %"), { target: { value: "6.5" } });
    fireEvent.change(screen.getByPlaceholderText("Loan years"), { target: { value: "30" } });
    fireEvent.click(screen.getByText("Calculate"));
    await waitFor(() => expect(screen.getByText(/Monthly payment:/)).toBeInTheDocument());
  });

  it("compares properties", async () => {
    render(<ToolsPage />);
    fireEvent.change(screen.getByPlaceholderText("IDs comma-separated"), { target: { value: "id1,id2" } });
    fireEvent.click(screen.getByText("Compare"));
    await waitFor(() => expect(screen.getByText(/Count:/)).toBeInTheDocument());
  });

  it("runs price analysis", async () => {
    render(<ToolsPage />);
    fireEvent.change(screen.getByPlaceholderText("Query (e.g., city or type)"), { target: { value: "Warsaw" } });
    const section = screen.getByText("Price Analysis").closest("section");
    if (!section) throw new Error("Missing Price Analysis section");
    fireEvent.click(within(section).getByRole("button", { name: "Analyze" }));
    await waitFor(() => expect(screen.getByText(/Average price:/)).toBeInTheDocument());
  });

  it("runs location analysis", async () => {
    render(<ToolsPage />);
    const section = screen.getByText("Location Analysis").closest("section");
    if (!section) throw new Error("Missing Location Analysis section");
    fireEvent.change(within(section).getByPlaceholderText("Property ID"), { target: { value: "p1" } });
    fireEvent.click(within(section).getByRole("button", { name: "Analyze" }));
    await waitFor(() => expect(screen.getByText(/City:/)).toBeInTheDocument());
  });

  it("runs valuation", async () => {
    render(<ToolsPage />);
    const inputs = screen.getAllByPlaceholderText("Property ID");
    fireEvent.change(inputs[0], { target: { value: "p1" } });
    fireEvent.click(screen.getByText("Estimate"));
    await waitFor(() => expect(screen.getByText(/Estimated value:/)).toBeInTheDocument());
  });

  it("runs legal check", async () => {
    render(<ToolsPage />);
    fireEvent.change(screen.getByPlaceholderText("Contract text"), { target: { value: "contract" } });
    const section = screen.getByText("Legal Check (CE Stub)").closest("section");
    if (!section) throw new Error("Missing Legal Check section");
    fireEvent.click(within(section).getByRole("button", { name: "Analyze" }));
    await waitFor(() => expect(screen.getByText(/Score:/)).toBeInTheDocument());
  });

  it("runs data enrichment", async () => {
    render(<ToolsPage />);
    fireEvent.change(screen.getByPlaceholderText("Address"), { target: { value: "Some St 1" } });
    fireEvent.click(screen.getByText("Enrich"));
    await waitFor(() => expect(screen.getByText(/Address:/)).toBeInTheDocument());
  });

  it("syncs CRM contact", async () => {
    render(<ToolsPage />);
    fireEvent.change(screen.getByPlaceholderText("Name"), { target: { value: "John" } });
    fireEvent.click(screen.getByText("Sync"));
    await waitFor(() => expect(screen.getByText(/Contact ID:/)).toBeInTheDocument());
  });

  it("renders and applies prompt templates", async () => {
    render(<ToolsPage />);
    await waitFor(() => expect(screen.getByText("Prompt Templates")).toBeInTheDocument());
    await waitFor(() => expect(screen.getByLabelText("Template picker")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("Variable property_address"), {
      target: { value: "Main St 10" },
    });
    fireEvent.change(screen.getByLabelText("Variable buyer_name"), { target: { value: "Alex" } });
    fireEvent.change(screen.getByLabelText("Variable agent_name"), { target: { value: "Maria" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));
    await waitFor(() => expect(screen.getByLabelText("Rendered template output")).toBeInTheDocument());
    const output = screen.getByLabelText("Rendered template output") as HTMLTextAreaElement;
    expect(output.value).toContain("Main St 10");
  });
});
