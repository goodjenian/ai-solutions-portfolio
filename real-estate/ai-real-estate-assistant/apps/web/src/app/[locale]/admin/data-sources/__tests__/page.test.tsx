import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import DataSourcesPage from "../page";
import { fetchFromPortal, getExcelSheets, ingestData, listPortals } from "@/lib/api";

jest.mock("@/lib/api", () => {
  class MockApiError extends Error {
    constructor(message: string, public status: number, public request_id?: string) {
      super(message);
      this.name = "ApiError";
    }
  }
  return {
    ingestData: jest.fn(async () => ({
      message: "Ingestion successful",
      properties_processed: 2,
      errors: [],
      source_type: "file",
      source_name: null,
    })),
    getExcelSheets: jest.fn(async () => ({
      file_url: "https://example.com/data.xlsx",
      sheet_names: ["Sheet1", "Sheet2"],
      default_sheet: "Sheet1",
      row_count: { Sheet1: 10, Sheet2: 20 },
    })),
    listPortals: jest.fn(async () => ({
      adapters: [
        {
          name: "overpass",
          display_name: "OpenStreetMap",
          configured: true,
          has_api_key: false,
          rate_limit: null,
        },
      ],
      count: 1,
    })),
    fetchFromPortal: jest.fn(async () => ({
      message: "Fetched 1 properties",
      portal: "overpass",
      properties_processed: 1,
      errors: [],
      source_type: "portal",
      source_name: "warsaw_rent",
    })),
    ApiError: MockApiError,
  };
});

describe("DataSourcesPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("ingests CSV from URL", async () => {
    render(<DataSourcesPage />);

    fireEvent.change(screen.getByLabelText("File URL"), {
      target: { value: "https://example.com/data.csv" },
    });
    fireEvent.change(screen.getByLabelText("Source Name"), {
      target: { value: "Q1 Imports" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Import Data" }));

    await waitFor(() => expect(ingestData).toHaveBeenCalled());
    expect((ingestData as jest.Mock).mock.calls[0][0]).toEqual({
      file_urls: ["https://example.com/data.csv"],
      sheet_name: undefined,
      header_row: 0,
      source_name: "Q1 Imports",
    });
    await waitFor(() =>
      expect(screen.getByText("Ingestion successful")).toBeInTheDocument()
    );
  });

  it("loads Excel sheets and ingests selected sheet", async () => {
    render(<DataSourcesPage />);

    fireEvent.change(screen.getByLabelText("File URL"), {
      target: { value: "https://example.com/data.xlsx" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Load Sheets" }));

    await waitFor(() => expect(getExcelSheets).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByLabelText("Select Sheet")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("Select Sheet"), {
      target: { value: "Sheet2" },
    });
    fireEvent.change(screen.getByLabelText("Header Row (0-indexed)"), {
      target: { value: "2" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Import Data" }));

    await waitFor(() => expect(ingestData).toHaveBeenCalled());
    expect((ingestData as jest.Mock).mock.calls[0][0]).toEqual({
      file_urls: ["https://example.com/data.xlsx"],
      sheet_name: "Sheet2",
      header_row: 2,
      source_name: undefined,
    });
  });

  it("fetches from portal", async () => {
    render(<DataSourcesPage />);

    fireEvent.click(screen.getByRole("button", { name: "Portal API" }));

    await waitFor(() => expect(listPortals).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByLabelText("Portal")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("City"), { target: { value: "Warsaw" } });

    fireEvent.click(screen.getByRole("button", { name: "Fetch from Portal" }));

    await waitFor(() => expect(fetchFromPortal).toHaveBeenCalled());
    expect((fetchFromPortal as jest.Mock).mock.calls[0][0]).toMatchObject({
      portal: "overpass",
      city: "Warsaw",
      listing_type: "rent",
      limit: 50,
    });
    await waitFor(() =>
      expect(screen.getByText("Fetched 1 properties")).toBeInTheDocument()
    );
  });
});
