import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NotificationSettings } from "../notification-settings";
import { getNotificationSettings, updateNotificationSettings } from "@/lib/api";
import { NotificationSettings as SettingsType } from "@/lib/types";

// Mock API
jest.mock("@/lib/api", () => ({
  getNotificationSettings: jest.fn(),
  updateNotificationSettings: jest.fn(),
}));

const mockSettings: SettingsType = {
  email_digest: true,
  frequency: "weekly",
  expert_mode: false,
  marketing_emails: false,
};

describe("NotificationSettings Component", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("renders loading state initially", () => {
    (getNotificationSettings as jest.Mock).mockImplementation(() => new Promise(() => {}));
    render(<NotificationSettings />);
    expect(screen.getByText("Loading settings...")).toBeInTheDocument();
  });

  it("renders settings form after loading", async () => {
    (getNotificationSettings as jest.Mock).mockResolvedValue(mockSettings);
    render(<NotificationSettings />);

    await waitFor(() => {
      expect(screen.getByText("Email Digests")).toBeInTheDocument();
    });

    // Check checkboxes
    const digestCheckbox = screen.getByLabelText(/Consumer Digest/i);
    expect(digestCheckbox).toBeChecked();

    const expertCheckbox = screen.getByLabelText(/Expert Mode/i);
    expect(expertCheckbox).not.toBeChecked();

    // Check select
    const frequencySelect = screen.getByLabelText(/Digest Frequency/i) as HTMLSelectElement;
    expect(frequencySelect.value).toBe("weekly");
  });

  it("handles error when loading fails", async () => {
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    (getNotificationSettings as jest.Mock).mockRejectedValue(new Error("API Error"));
    render(<NotificationSettings />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load settings. Please try again.")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
    expect(errorSpy).not.toHaveBeenCalled();
    errorSpy.mockRestore();
  });

  it("toggles checkboxes", async () => {
    (getNotificationSettings as jest.Mock).mockResolvedValue(mockSettings);
    render(<NotificationSettings />);

    await waitFor(() => {
      expect(screen.getByText("Email Digests")).toBeInTheDocument();
    });

    const expertCheckbox = screen.getByLabelText(/Expert Mode/i);
    fireEvent.click(expertCheckbox);
    expect(expertCheckbox).toBeChecked();
  });

  it("changes frequency", async () => {
    (getNotificationSettings as jest.Mock).mockResolvedValue(mockSettings);
    render(<NotificationSettings />);

    await waitFor(() => {
      expect(screen.getByText("Email Digests")).toBeInTheDocument();
    });

    const frequencySelect = screen.getByLabelText(/Digest Frequency/i);
    fireEvent.change(frequencySelect, { target: { value: "daily" } });
    expect((frequencySelect as HTMLSelectElement).value).toBe("daily");
  });

  it("saves settings successfully", async () => {
    (getNotificationSettings as jest.Mock).mockResolvedValue(mockSettings);
    (updateNotificationSettings as jest.Mock).mockImplementation(async (s) => s);

    render(<NotificationSettings />);

    await waitFor(() => {
      expect(screen.getByText("Email Digests")).toBeInTheDocument();
    });

    // Change something
    const expertCheckbox = screen.getByLabelText(/Expert Mode/i);
    fireEvent.click(expertCheckbox);

    // Click Save
    const saveButton = screen.getByRole("button", { name: /Save Preferences/i });
    fireEvent.click(saveButton);

    expect(saveButton).toBeDisabled();
    expect(screen.getByText("Saving...")).toBeInTheDocument();

    await waitFor(() => {
      expect(updateNotificationSettings).toHaveBeenCalledWith({
        ...mockSettings,
        expert_mode: true,
      });
      expect(screen.getByText("Settings saved successfully.")).toBeInTheDocument();
    });
  });

  it("handles save error", async () => {
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    (getNotificationSettings as jest.Mock).mockResolvedValue(mockSettings);
    (updateNotificationSettings as jest.Mock).mockRejectedValue(new Error("Save failed"));

    render(<NotificationSettings />);

    await waitFor(() => {
      expect(screen.getByText("Email Digests")).toBeInTheDocument();
    });

    const saveButton = screen.getByRole("button", { name: /Save Preferences/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText("Failed to save settings. Please try again.")).toBeInTheDocument();
    });
    expect(errorSpy).not.toHaveBeenCalled();
    errorSpy.mockRestore();
  });
});
