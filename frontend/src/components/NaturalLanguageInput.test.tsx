import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axios from "axios";
import NaturalLanguageInput from "./NaturalLanguageInput";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe("NaturalLanguageInput Component", () => {
  const mockResponse = {
    action_plan: {
      action: "list_containers",
      parameters: {},
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock successful API response
    mockedAxios.post.mockResolvedValue({ data: mockResponse });

    // Clear localStorage
    localStorage.clear();
  });

  test("renders input field and button correctly", () => {
    render(<NaturalLanguageInput />);

    // Check if the input field is rendered (Autocomplete with freeSolo renders as combobox)
    const inputElement = screen.getByRole("combobox");
    expect(inputElement).toBeInTheDocument();

    // Check if the send button is rendered and disabled initially
    const sendButton = screen.getByRole("button", { name: /send/i });
    expect(sendButton).toBeInTheDocument();
    expect(sendButton).toBeDisabled();
  });

  test("enables send button when input is provided", async () => {
    render(<NaturalLanguageInput />);

    // Get the input field
    const inputElement = screen.getByRole("combobox");

    // Type in the input field
    await act(async () => {
      await userEvent.type(inputElement, "List all containers");
    });

    // Check if the send button is enabled
    const sendButton = screen.getByRole("button", { name: /send/i });
    expect(sendButton).not.toBeDisabled();
  });

  test("sends command and displays response", async () => {
    render(<NaturalLanguageInput />);

    // Get the input field and type in it
    const inputElement = screen.getByRole("combobox");
    await act(async () => {
      await userEvent.type(inputElement, "List all containers");
    });

    // Click the send button
    const sendButton = screen.getByRole("button", { name: /send/i });
    await act(async () => {
      fireEvent.click(sendButton);
    });

    // Check if the API was called correctly
    expect(mockedAxios.post).toHaveBeenCalledWith("/nlp/parse", {
      command: "List all containers",
    });

    // Wait for the response to be displayed
    await waitFor(() => {
      expect(screen.getByText("Response:")).toBeInTheDocument();
    });

    // Check if the response content is displayed
    const responseElement = screen.getByText(/list_containers/i);
    expect(responseElement).toBeInTheDocument();
  });

  test("displays error message when API call fails", async () => {
    // Mock failed API response
    mockedAxios.post.mockRejectedValueOnce({
      response: { data: { detail: "Failed to process command" } },
    });

    render(<NaturalLanguageInput />);

    // Get the input field and type in it
    const inputElement = screen.getByRole("combobox");
    await act(async () => {
      await userEvent.type(inputElement, "Invalid command");
    });

    // Click the send button
    const sendButton = screen.getByRole("button", { name: /send/i });
    await act(async () => {
      fireEvent.click(sendButton);
    });

    // Wait for the error message to be displayed
    await waitFor(() => {
      expect(screen.getByText("Failed to process command")).toBeInTheDocument();
    });
  });

  test("shows and hides command history", async () => {
    // Set up localStorage with command history
    localStorage.setItem(
      "commandHistory",
      JSON.stringify(["List containers", "Deploy WordPress"])
    );

    render(<NaturalLanguageInput />);

    // Click the history chip
    const historyChip = screen.getByText("History");
    fireEvent.click(historyChip);

    // Check if history items are displayed
    expect(screen.getByText("List containers")).toBeInTheDocument();
    expect(screen.getByText("Deploy WordPress")).toBeInTheDocument();

    // Click the history chip again to hide history
    fireEvent.click(historyChip);

    // Check if history items are hidden
    await waitFor(() => {
      expect(screen.queryByText("List containers")).not.toBeInTheDocument();
    });
  });

  test("shows and hides suggestions", async () => {
    render(<NaturalLanguageInput />);

    // Click the suggestions chip
    const suggestionsChip = screen.getByText("Suggestions");
    fireEvent.click(suggestionsChip);

    // Check if suggestion items are displayed
    expect(screen.getByText("Deploy a WordPress stack")).toBeInTheDocument();
    expect(screen.getByText("Start all containers")).toBeInTheDocument();

    // Click the suggestions chip again to hide suggestions
    fireEvent.click(suggestionsChip);

    // Check if suggestion items are hidden
    await waitFor(() => {
      expect(
        screen.queryByText("Deploy a WordPress stack")
      ).not.toBeInTheDocument();
    });
  });

  test("adds command to history when sent", async () => {
    render(<NaturalLanguageInput />);

    // Get the input field and type in it
    const inputElement = screen.getByRole("combobox");
    await act(async () => {
      await userEvent.type(inputElement, "List all containers");
    });

    // Click the send button
    const sendButton = screen.getByRole("button", { name: /send/i });
    await act(async () => {
      fireEvent.click(sendButton);
    });

    // Wait for the response
    await waitFor(() => {
      expect(screen.getByText("Response:")).toBeInTheDocument();
    });

    // Click the history chip to show history
    const historyChip = screen.getByText("History");
    fireEvent.click(historyChip);

    // Check if the command was added to history (use getAllByText to handle multiple elements)
    const historyElements = screen.getAllByText("List all containers");
    expect(historyElements.length).toBeGreaterThan(0);

    // Check if localStorage was updated
    const storedHistory = JSON.parse(
      localStorage.getItem("commandHistory") || "[]"
    );
    expect(storedHistory).toContain("List all containers");
  });

  test("fills input when clicking on a suggestion", async () => {
    render(<NaturalLanguageInput />);

    // Click the suggestions chip
    const suggestionsChip = screen.getByText("Suggestions");
    fireEvent.click(suggestionsChip);

    // Click on a suggestion
    const suggestion = screen.getByText("Deploy a WordPress stack");
    fireEvent.click(suggestion);

    // Check if the input field was filled with the suggestion
    const inputElement = screen.getByRole("combobox");
    expect(inputElement).toHaveValue("Deploy a WordPress stack");

    // Check if suggestions are hidden
    await waitFor(() => {
      expect(
        screen.queryByText("Start all containers")
      ).not.toBeInTheDocument();
    });
  });
});
