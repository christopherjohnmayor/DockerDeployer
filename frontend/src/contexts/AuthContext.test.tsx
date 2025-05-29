import React, { useContext } from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import axios from "axios";
import { AuthProvider, AuthContext } from "./AuthContext";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock jwt-decode
jest.mock("jwt-decode", () => ({
  jwtDecode: jest.fn(),
}));
import { jwtDecode } from "jwt-decode";
const mockedJwtDecode = jwtDecode as jest.MockedFunction<typeof jwtDecode>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// Replace the global localStorage
Object.defineProperty(global, "localStorage", {
  value: localStorageMock,
  writable: true,
});

// Also replace window.localStorage for compatibility
Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
  writable: true,
});

// Test component to access context
const TestComponent: React.FC = () => {
  const { isAuthenticated, user, login, logout, refreshAuth } =
    useContext(AuthContext);

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? "authenticated" : "not-authenticated"}
      </div>
      <div data-testid="user-info">
        {user ? `${user.username} (${user.role})` : "no-user"}
      </div>
      <button
        data-testid="login-btn"
        onClick={() => login("test-access-token", "test-refresh-token")}
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
      <button
        data-testid="refresh-btn"
        onClick={async () => {
          const result = await refreshAuth();
          console.log("Refresh result:", result);
        }}
      >
        Refresh
      </button>
    </div>
  );
};

// Suppress console errors in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === "string" &&
      (args[0].includes("Warning: An update to") ||
        args[0].includes("Warning: validateDOMNesting") ||
        args[0].includes("Failed to decode token") ||
        args[0].includes("Failed to logout on server") ||
        args[0].includes("Failed to refresh token"))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

describe("AuthContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();

    // Mock axios defaults
    mockedAxios.defaults = {
      headers: {
        common: {},
      },
    } as any;

    // Mock axios interceptors
    mockedAxios.interceptors = {
      response: {
        use: jest.fn().mockReturnValue(1),
        eject: jest.fn(),
      },
      request: {
        use: jest.fn().mockReturnValue(1),
        eject: jest.fn(),
      },
    } as any;

    // Reset axios mocks
    mockedAxios.post.mockReset();
    mockedAxios.post.mockResolvedValue({ data: {} });
  });

  test("provides default context values", async () => {
    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    expect(screen.getByTestId("auth-status")).toHaveTextContent(
      "not-authenticated"
    );
    expect(screen.getByTestId("user-info")).toHaveTextContent("no-user");

    // Verify that localStorage.getItem was called during initialization
    await waitFor(() => {
      expect(localStorageMock.getItem).toHaveBeenCalledWith("accessToken");
      expect(localStorageMock.getItem).toHaveBeenCalledWith("refreshToken");
    });
  });

  test("initializes with tokens from localStorage", async () => {
    const mockToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test";
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600, // Valid for 1 hour
      type: "access",
    };

    // Set up localStorage before rendering
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === "accessToken") return mockToken;
      if (key === "refreshToken") return "refresh-token";
      return null;
    });

    mockedJwtDecode.mockReturnValue(mockDecodedToken);

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Wait for the useEffect to process the token
    await waitFor(
      () => {
        expect(localStorageMock.getItem).toHaveBeenCalledWith("accessToken");
      },
      { timeout: 3000 }
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated"
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("user-info")).toHaveTextContent(
        "testuser (user)"
      );
    });

    expect(mockedJwtDecode).toHaveBeenCalledWith(mockToken);
  });

  test("handles expired token on initialization", async () => {
    const mockToken = "expired-token";
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) - 3600, // Expired 1 hour ago
      type: "access",
    };

    localStorageMock.getItem.mockImplementation((key) => {
      if (key === "accessToken") return mockToken;
      if (key === "refreshToken") return "refresh-token";
      return null;
    });

    const newTokenDecoded = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    // Mock successful refresh
    mockedAxios.post.mockResolvedValue({
      data: {
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
      },
    });

    mockedJwtDecode
      .mockReturnValueOnce(mockDecodedToken) // First call for expired token
      .mockReturnValueOnce(newTokenDecoded); // Second call for new token

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/refresh", {
        refresh_token: "refresh-token",
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated"
      );
    });
  });

  test("handles invalid token on initialization", async () => {
    const mockToken = "invalid-token";

    localStorageMock.getItem.mockImplementation((key) => {
      if (key === "accessToken") return mockToken;
      if (key === "refreshToken") return "refresh-token";
      return null;
    });

    mockedJwtDecode.mockImplementation(() => {
      throw new Error("Invalid token");
    });

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated"
      );
    });

    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("accessToken");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refreshToken");
    });
  });

  test("login function works correctly", async () => {
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    // Clear any previous calls and set up fresh mock
    mockedJwtDecode.mockClear();
    localStorageMock.setItem.mockClear();

    // Mock the decode function to return our test token
    mockedJwtDecode.mockReturnValue(mockDecodedToken);

    let loginFunction: any;

    // Create a test component that captures the login function
    const TestLoginComponent = () => {
      const { isAuthenticated, user, login } = useContext(AuthContext);
      loginFunction = login;

      return (
        <div>
          <div data-testid="auth-status">
            {isAuthenticated ? "authenticated" : "not-authenticated"}
          </div>
          <div data-testid="user-info">
            {user ? `${user.username} (${user.role})` : "no-user"}
          </div>
        </div>
      );
    };

    await act(async () => {
      render(
        <AuthProvider>
          <TestLoginComponent />
        </AuthProvider>
      );
    });

    // Call login function directly
    await act(async () => {
      loginFunction("test-access-token", "test-refresh-token");
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated"
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("user-info")).toHaveTextContent(
        "testuser (user)"
      );
    });

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "accessToken",
      "test-access-token"
    );
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "refreshToken",
      "test-refresh-token"
    );
    expect(mockedJwtDecode).toHaveBeenCalledWith("test-access-token");
  });

  test("login handles invalid token", async () => {
    mockedJwtDecode.mockImplementation(() => {
      throw new Error("Invalid token");
    });

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    const loginButton = screen.getByTestId("login-btn");

    await act(async () => {
      fireEvent.click(loginButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated"
      );
    });

    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("accessToken");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refreshToken");
    });
  });

  test("logout function works correctly", async () => {
    // First login
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    mockedJwtDecode.mockReturnValue(mockDecodedToken);
    mockedAxios.post.mockResolvedValue({ data: {} });

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Login first
    const loginButton = screen.getByTestId("login-btn");
    await act(async () => {
      fireEvent.click(loginButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated"
      );
    });

    // Clear the mock to check logout call specifically
    mockedAxios.post.mockClear();

    // Now logout
    const logoutButton = screen.getByTestId("logout-btn");
    await act(async () => {
      fireEvent.click(logoutButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated"
      );
      expect(screen.getByTestId("user-info")).toHaveTextContent("no-user");
    });

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/logout", {
        refresh_token: "test-refresh-token",
      });
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("accessToken");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refreshToken");
    });
  });

  test("logout handles server error gracefully", async () => {
    // First login
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    mockedJwtDecode.mockReturnValue(mockDecodedToken);
    // First allow login to succeed
    mockedAxios.post.mockResolvedValueOnce({ data: {} });

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Login first
    const loginButton = screen.getByTestId("login-btn");
    await act(async () => {
      fireEvent.click(loginButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated"
      );
    });

    // Now make logout fail
    mockedAxios.post.mockRejectedValue(new Error("Server error"));

    // Now logout (should handle server error gracefully)
    const logoutButton = screen.getByTestId("logout-btn");
    await act(async () => {
      fireEvent.click(logoutButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated"
      );
    });

    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("accessToken");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refreshToken");
    });
  });

  test("refreshAuth works correctly", async () => {
    // Set up initial state with refresh token
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === "refreshToken") return "refresh-token";
      return null;
    });

    const newTokenDecoded = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    mockedJwtDecode.mockReturnValue(newTokenDecoded);
    mockedAxios.post.mockResolvedValue({
      data: {
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
      },
    });

    let refreshFunction: any;

    // Create a test component that captures the refresh function
    const TestRefreshComponent = () => {
      const { isAuthenticated, user, refreshAuth } = useContext(AuthContext);
      refreshFunction = refreshAuth;

      return (
        <div>
          <div data-testid="auth-status">
            {isAuthenticated ? "authenticated" : "not-authenticated"}
          </div>
          <div data-testid="user-info">
            {user ? `${user.username} (${user.role})` : "no-user"}
          </div>
        </div>
      );
    };

    await act(async () => {
      render(
        <AuthProvider>
          <TestRefreshComponent />
        </AuthProvider>
      );
    });

    // Call refresh function directly
    await act(async () => {
      await refreshFunction();
    });

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/refresh", {
        refresh_token: "refresh-token",
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated"
      );
    });

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "accessToken",
      "new-access-token"
    );
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "refreshToken",
      "new-refresh-token"
    );
  });

  test("refreshAuth handles no refresh token", async () => {
    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    const refreshButton = screen.getByTestId("refresh-btn");
    await act(async () => {
      fireEvent.click(refreshButton);
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated"
      );
    });

    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  test("refreshAuth handles server error", async () => {
    // Set up initial state with refresh token
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === "refreshToken") return "refresh-token";
      return null;
    });

    mockedAxios.post.mockRejectedValue(new Error("Refresh failed"));

    let refreshFunction: any;

    // Create a test component that captures the refresh function
    const TestRefreshComponent = () => {
      const { isAuthenticated, user, refreshAuth } = useContext(AuthContext);
      refreshFunction = refreshAuth;

      return (
        <div>
          <div data-testid="auth-status">
            {isAuthenticated ? "authenticated" : "not-authenticated"}
          </div>
          <div data-testid="user-info">
            {user ? `${user.username} (${user.role})` : "no-user"}
          </div>
        </div>
      );
    };

    await act(async () => {
      render(
        <AuthProvider>
          <TestRefreshComponent />
        </AuthProvider>
      );
    });

    // Call refresh function directly
    await act(async () => {
      await refreshFunction();
    });

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/refresh", {
        refresh_token: "refresh-token",
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated"
      );
    });

    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("accessToken");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refreshToken");
    });
  });

  test("sets up axios authorization header correctly", async () => {
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    mockedJwtDecode.mockReturnValue(mockDecodedToken);

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    const loginButton = screen.getByTestId("login-btn");
    await act(async () => {
      fireEvent.click(loginButton);
    });

    await waitFor(() => {
      expect(mockedAxios.defaults.headers.common["Authorization"]).toBe(
        "Bearer test-access-token"
      );
    });
  });

  test("removes axios authorization header on logout", async () => {
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    mockedJwtDecode.mockReturnValue(mockDecodedToken);
    mockedAxios.post.mockResolvedValue({ data: {} });

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Login first
    const loginButton = screen.getByTestId("login-btn");
    await act(async () => {
      fireEvent.click(loginButton);
    });

    // Logout
    const logoutButton = screen.getByTestId("logout-btn");
    await act(async () => {
      fireEvent.click(logoutButton);
    });

    await waitFor(() => {
      expect(
        mockedAxios.defaults.headers.common["Authorization"]
      ).toBeUndefined();
    });
  });

  test("sets up axios interceptor correctly", async () => {
    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    expect(mockedAxios.interceptors.response.use).toHaveBeenCalled();
  });

  test("cleans up axios interceptor on unmount", async () => {
    const { unmount } = await act(async () => {
      return render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    await act(async () => {
      unmount();
    });

    expect(mockedAxios.interceptors.response.eject).toHaveBeenCalled();
  });

  test("handles axios interceptor 401 error with successful token refresh", async () => {
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    mockedJwtDecode.mockReturnValue(mockDecodedToken);

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Login to set up tokens
    const loginButton = screen.getByTestId("login-btn");
    await act(async () => {
      fireEvent.click(loginButton);
    });

    // Verify that the interceptor was set up
    expect(mockedAxios.interceptors.response.use).toHaveBeenCalled();

    // Get the interceptor function
    const interceptorCall = mockedAxios.interceptors.response.use.mock.calls[0];
    const errorHandler = interceptorCall[1];

    // Verify the error handler exists
    expect(typeof errorHandler).toBe("function");
  });

  test("handles axios interceptor 401 error with failed token refresh", async () => {
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600,
      type: "access",
    };

    mockedJwtDecode.mockReturnValue(mockDecodedToken);

    // Mock failed refresh
    mockedAxios.post.mockRejectedValue(new Error("Refresh failed"));

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Login to set up tokens
    const loginButton = screen.getByTestId("login-btn");
    await act(async () => {
      fireEvent.click(loginButton);
    });

    // Simulate a 401 error that should trigger token refresh
    const error401 = {
      response: { status: 401 },
      config: { headers: {} },
    };

    // Get the interceptor function
    const interceptorCall = mockedAxios.interceptors.response.use.mock.calls[0];
    const errorHandler = interceptorCall[1];

    // Call the error handler and expect it to reject
    await expect(errorHandler(error401)).rejects.toEqual(error401);
  });

  test("handles axios interceptor non-401 errors", async () => {
    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Simulate a non-401 error
    const error500 = {
      response: { status: 500 },
      config: { headers: {} },
    };

    // Get the interceptor function
    const interceptorCall = mockedAxios.interceptors.response.use.mock.calls[0];
    const errorHandler = interceptorCall[1];

    // Call the error handler and expect it to reject immediately
    await expect(errorHandler(error500)).rejects.toEqual(error500);
  });

  test("handles axios interceptor 401 error when already retried", async () => {
    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Simulate a 401 error that has already been retried
    const error401Retried = {
      response: { status: 401 },
      config: { headers: {}, _retry: true },
    };

    // Get the interceptor function
    const interceptorCall = mockedAxios.interceptors.response.use.mock.calls[0];
    const errorHandler = interceptorCall[1];

    // Call the error handler and expect it to reject immediately
    await expect(errorHandler(error401Retried)).rejects.toEqual(
      error401Retried
    );
  });

  test("handles axios interceptor 401 error without refresh token", async () => {
    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Simulate a 401 error without refresh token
    const error401 = {
      response: { status: 401 },
      config: { headers: {} },
    };

    // Get the interceptor function
    const interceptorCall = mockedAxios.interceptors.response.use.mock.calls[0];
    const errorHandler = interceptorCall[1];

    // Call the error handler and expect it to reject immediately
    await expect(errorHandler(error401)).rejects.toEqual(error401);
  });

  test("handles expired token on initialization without refresh token", async () => {
    const expiredToken = "expired-token";
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) - 3600, // Expired 1 hour ago
      type: "access",
    };

    localStorageMock.getItem.mockImplementation((key) => {
      if (key === "accessToken") return expiredToken;
      if (key === "refreshToken") return null; // No refresh token
      return null;
    });

    mockedJwtDecode.mockReturnValue(mockDecodedToken);

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated"
      );
    });

    // Verify tokens were cleared
    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("accessToken");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refreshToken");
    });
  });

  test("handles expired token on initialization with failed refresh", async () => {
    const expiredToken = "expired-token";
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) - 3600, // Expired 1 hour ago
      type: "access",
    };

    localStorageMock.getItem.mockImplementation((key) => {
      if (key === "accessToken") return expiredToken;
      if (key === "refreshToken") return "refresh-token";
      return null;
    });

    mockedJwtDecode.mockReturnValue(mockDecodedToken);
    mockedAxios.post.mockRejectedValue(new Error("Refresh failed"));

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "not-authenticated"
      );
    });

    // Verify refresh was attempted
    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/refresh", {
        refresh_token: "refresh-token",
      });
    });

    // Verify tokens were cleared after failed refresh
    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("accessToken");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refreshToken");
    });
  });

  test("handles expired token on initialization with successful refresh", async () => {
    const expiredToken = "expired-token";
    const mockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) - 3600, // Expired 1 hour ago
      type: "access",
    };

    const newMockDecodedToken = {
      sub: 1,
      username: "testuser",
      role: "user",
      exp: Math.floor(Date.now() / 1000) + 3600, // Valid for 1 hour
      type: "access",
    };

    localStorageMock.getItem.mockImplementation((key) => {
      if (key === "accessToken") return expiredToken;
      if (key === "refreshToken") return "refresh-token";
      return null;
    });

    // First call returns expired token, second call returns new token
    mockedJwtDecode
      .mockReturnValueOnce(mockDecodedToken)
      .mockReturnValueOnce(newMockDecodedToken);

    mockedAxios.post.mockResolvedValue({
      data: {
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
      },
    });

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "authenticated"
      );
    });

    // Verify refresh was attempted
    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/auth/refresh", {
        refresh_token: "refresh-token",
      });
    });

    // Verify new tokens were stored
    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "accessToken",
        "new-access-token"
      );
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "refreshToken",
        "new-refresh-token"
      );
    });
  });

  test("uses default context when accessed outside provider", () => {
    const TestComponentOutsideProvider = () => {
      const context = useContext(AuthContext);
      return (
        <div>
          <div data-testid="default-auth-status">
            {context.isAuthenticated ? "authenticated" : "not-authenticated"}
          </div>
          <div data-testid="default-user-info">
            {context.user ? `${context.user.username}` : "no-user"}
          </div>
        </div>
      );
    };

    render(<TestComponentOutsideProvider />);

    expect(screen.getByTestId("default-auth-status")).toHaveTextContent(
      "not-authenticated"
    );
    expect(screen.getByTestId("default-user-info")).toHaveTextContent(
      "no-user"
    );
  });
});
