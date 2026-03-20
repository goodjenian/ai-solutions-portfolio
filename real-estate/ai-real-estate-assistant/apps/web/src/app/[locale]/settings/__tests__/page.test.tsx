import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import SettingsPage from "../page";
import { getModelsCatalog, testModelRuntime, ApiError } from "@/lib/api";

// Mock API
jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  getNotificationSettings: jest.fn(),
  updateNotificationSettings: jest.fn(),
  getModelsCatalog: jest.fn(),
  testModelRuntime: jest.fn(),
  getModelPreferences: jest.fn(),
  updateModelPreferences: jest.fn(),
}));

// Mock child component to simplify integration test
jest.mock("@/components/settings/notification-settings", () => ({
  NotificationSettings: () => <div data-testid="notification-settings">Notification Settings Component</div>,
}));

jest.mock("@/components/settings/identity-settings", () => ({
  IdentitySettings: () => <div data-testid="identity-settings">Identity Settings Component</div>,
}));

jest.mock("@/components/settings/model-settings", () => ({
  ModelSettings: () => <div data-testid="model-settings">Model Settings Component</div>,
}));

describe("SettingsPage", () => {
  const mockGetModelsCatalog = getModelsCatalog as jest.Mock;
  const mockTestModelRuntime = testModelRuntime as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetModelsCatalog.mockImplementation(() => new Promise(() => {}));
  });

  it("renders page title and description", () => {
    render(<SettingsPage />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(screen.getByText("Manage your account settings and notification preferences.")).toBeInTheDocument();
  });

  it("renders notification settings section", () => {
    render(<SettingsPage />);
    expect(screen.getByText("Identity")).toBeInTheDocument();
    expect(screen.getByTestId("identity-settings")).toBeInTheDocument();
    expect(screen.getByText("Notifications")).toBeInTheDocument();
    expect(screen.getByTestId("notification-settings")).toBeInTheDocument();
  });

  it("renders models section and loads catalog", async () => {
    mockGetModelsCatalog.mockResolvedValueOnce([
      {
        name: "openai",
        display_name: "OpenAI",
        is_local: false,
        requires_api_key: true,
        models: [
          {
            id: "gpt-4o",
            display_name: "GPT-4o",
            provider_name: "OpenAI",
            context_window: 128000,
            pricing: { input_price_per_1m: 2.5, output_price_per_1m: 10, currency: "USD" },
            capabilities: ["streaming", "vision"],
            description: null,
            recommended_for: [],
          },
        ],
      },
    ]);

    render(<SettingsPage />);

    expect(screen.getByText("Models")).toBeInTheDocument();
    expect(screen.getByTestId("model-settings")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh Catalog" })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("OpenAI")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Refresh Catalog" })).toBeEnabled();
    expect(screen.getByText("GPT-4o")).toBeInTheDocument();
    expect(screen.getByText("gpt-4o")).toBeInTheDocument();
    expect(screen.getByText("128,000")).toBeInTheDocument();
    expect(screen.getByText("USD 2.50")).toBeInTheDocument();
    expect(screen.getByText("USD 10.00")).toBeInTheDocument();
    expect(screen.getByText("streaming, vision")).toBeInTheDocument();
  });

  it("runs targeted runtime test for a local provider", async () => {
    mockGetModelsCatalog.mockResolvedValueOnce([
      {
        name: "ollama",
        display_name: "Ollama",
        is_local: true,
        requires_api_key: false,
        runtime_available: false,
        available_models: [],
        models: [
          {
            id: "llama3.3:8b",
            display_name: "Llama 3.3 8B",
            provider_name: "Ollama",
            context_window: 128000,
            pricing: null,
            capabilities: [],
            description: null,
            recommended_for: [],
          },
        ],
      },
    ]);
    mockTestModelRuntime.mockResolvedValueOnce({
      provider: "ollama",
      is_local: true,
      runtime_available: true,
      available_models: ["llama3.3:8b"],
      runtime_error: null,
    });

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Test Connection" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Test Connection" }));

    await waitFor(() => {
      expect(mockTestModelRuntime).toHaveBeenCalledWith("ollama");
      expect(screen.getByText(/Connection successful/i)).toBeInTheDocument();
    });
  });

  it("refreshes catalog without clearing existing table", async () => {
    mockGetModelsCatalog
      .mockResolvedValueOnce([
        {
          name: "openai",
          display_name: "OpenAI",
          is_local: false,
          requires_api_key: true,
          models: [
            {
              id: "gpt-4o",
              display_name: "GPT-4o",
              provider_name: "OpenAI",
              context_window: 128000,
              pricing: { input_price_per_1m: 2.5, output_price_per_1m: 10, currency: "USD" },
              capabilities: ["streaming", "vision"],
              description: null,
              recommended_for: [],
            },
          ],
        },
      ])
      .mockResolvedValueOnce([
        {
          name: "ollama",
          display_name: "Ollama",
          is_local: true,
          requires_api_key: false,
          runtime_available: true,
          available_models: ["llama3.3:8b"],
          models: [
            {
              id: "llama3.3:8b",
              display_name: "Llama 3.3 8B",
              provider_name: "Ollama",
              context_window: 128000,
              pricing: null,
              capabilities: [],
              description: null,
              recommended_for: [],
            },
          ],
        },
      ]);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("OpenAI")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Refresh Catalog" }));

    expect(screen.getByRole("button", { name: "Refreshing..." })).toBeInTheDocument();
    expect(screen.getByText("OpenAI")).toBeInTheDocument();

    await waitFor(() => {
      expect(mockGetModelsCatalog).toHaveBeenCalledTimes(2);
      expect(screen.getByText("Ollama")).toBeInTheDocument();
    });
  });

  it("shows retry on catalog load failure", async () => {
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    mockGetModelsCatalog.mockRejectedValueOnce(new ApiError("Failed to load model catalog. Please try again.", 500));

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load model catalog. Please try again.")).toBeInTheDocument();
    });
    expect(errorSpy).not.toHaveBeenCalled();
    errorSpy.mockRestore();

    mockGetModelsCatalog.mockResolvedValueOnce([]);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(mockGetModelsCatalog).toHaveBeenCalledTimes(2);
    });
  });

  it("shows no models available when catalog is empty", async () => {
    mockGetModelsCatalog.mockResolvedValueOnce([]);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("No models available.")).toBeInTheDocument();
    });
  });

  it("renders model rows with missing pricing and capabilities", async () => {
    mockGetModelsCatalog.mockResolvedValueOnce([
      {
        name: "ollama",
        display_name: "Ollama",
        is_local: true,
        requires_api_key: false,
        models: [
          {
            id: "llama3",
            display_name: "Llama 3",
            provider_name: "Ollama",
            context_window: 8192,
            pricing: null,
            capabilities: [],
            description: null,
            recommended_for: [],
          },
        ],
      },
    ]);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Ollama")).toBeInTheDocument();
    });

    expect(screen.getByText("Local")).toBeInTheDocument();
    expect(screen.getByText("No API key required")).toBeInTheDocument();
    expect(screen.getByText(/Local models run on your machine/i)).toBeInTheDocument();
    expect(screen.getByText("Local models & offline usage")).toBeInTheDocument();
    expect(screen.getByText(/Local runtime status is unknown/i)).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("renders local runtime unavailable status and setup steps", async () => {
    mockGetModelsCatalog.mockResolvedValueOnce([
      {
        name: "ollama",
        display_name: "Ollama",
        is_local: true,
        requires_api_key: false,
        runtime_available: false,
        available_models: [],
        models: [
          {
            id: "llama3.3:8b",
            display_name: "Llama 3.3 8B",
            provider_name: "Ollama",
            context_window: 128000,
            pricing: null,
            capabilities: [],
            description: null,
            recommended_for: [],
          },
        ],
      },
    ]);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Local runtime not detected/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Install Ollama/i)).toBeInTheDocument();
    expect(screen.getByText(/ollama\.com\/download/i)).toBeInTheDocument();
    expect(screen.getByText(/ollama pull llama3\.3:8b/i)).toBeInTheDocument();
    expect(screen.getByText(/host\.docker\.internal:11434/i)).toBeInTheDocument();
  });

  it("renders local runtime available status and downloaded models list", async () => {
    mockGetModelsCatalog.mockResolvedValueOnce([
      {
        name: "ollama",
        display_name: "Ollama",
        is_local: true,
        requires_api_key: false,
        runtime_available: true,
        available_models: ["llama3.3:8b", "mistral:7b"],
        models: [
          {
            id: "llama3.3:8b",
            display_name: "Llama 3.3 8B",
            provider_name: "Ollama",
            context_window: 128000,
            pricing: null,
            capabilities: [],
            description: null,
            recommended_for: [],
          },
        ],
      },
    ]);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Local runtime detected\. Downloaded models: 2\./i)).toBeInTheDocument();
    });

    expect(screen.getByText("Downloaded models")).toBeInTheDocument();
    expect(screen.getByText(/llama3\.3:8b, mistral:7b/i)).toBeInTheDocument();
  });
});
