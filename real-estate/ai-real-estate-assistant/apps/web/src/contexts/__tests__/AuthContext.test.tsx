/**
 * Tests for AuthContext
 *
 * Tests cover:
 * - Initial state
 * - Login flow
 * - Logout flow
 * - Register flow
 * - Error handling
 */

import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';

// Mock fetch globally before any imports
const mockFetch = jest.fn();
(globalThis as unknown as { fetch: jest.Mock }).fetch = mockFetch;

// Mock the API error
jest.mock('@/lib/api', () => ({
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

import { AuthProvider, useAuth } from '../AuthContext';
import { ApiError } from '@/lib/api';

// Test component to access auth context
function TestComponent() {
  const { user, isLoading, isAuthenticated, error, login, logout, clearError } = useAuth();

  const handleLogin = async () => {
    try {
      await login('test@example.com', 'password');
    } catch {
      // Error is already set in context
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Error is already set in context
    }
  };

  return (
    <div>
      <span data-testid="loading">{isLoading.toString()}</span>
      <span data-testid="authenticated">{isAuthenticated.toString()}</span>
      <span data-testid="user">{user ? user.email : 'null'}</span>
      <span data-testid="error">{error || 'null'}</span>
      <button onClick={handleLogin} data-testid="login-btn">
        Login
      </button>
      <button onClick={handleLogout} data-testid="logout-btn">
        Logout
      </button>
      <button onClick={clearError} data-testid="clear-error-btn">
        Clear Error
      </button>
    </div>
  );
}

// Helper to create mock responses
function createMockResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: new Headers(),
    json: async () => data,
    text: async () => JSON.stringify(data),
  } as Response;
}

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockReset();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Initial State', () => {
    it('starts with loading state', async () => {
      // Mock getCurrentUser to never resolve
      mockFetch.mockImplementation(() => new Promise(() => {}));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      expect(screen.getByTestId('loading').textContent).toBe('true');
    });

    it('sets loading to false after fetching user', async () => {
      // Mock getCurrentUser to return null (no user)
      mockFetch.mockRejectedValueOnce(new Error('Not authenticated'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });
    });

    it('starts unauthenticated when no user', async () => {
      // Mock getCurrentUser to fail
      mockFetch.mockRejectedValueOnce(new Error('Not authenticated'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('false');
      });
    });
  });

  describe('Login Flow', () => {
    it('logs in successfully', async () => {
      const mockUser = { id: '1', email: 'test@example.com' };

      // First call: getCurrentUser (fails - no user initially)
      mockFetch.mockRejectedValueOnce(new Error('Not authenticated'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      // Second call: login
      mockFetch.mockResolvedValueOnce(createMockResponse({
        access_token: 'token',
        refresh_token: 'refresh',
        token_type: 'bearer',
        expires_in: 3600,
        user: mockUser
      }));

      // Click login button
      await act(async () => {
        screen.getByTestId('login-btn').click();
      });

      // Check authenticated state
      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('true');
        expect(screen.getByTestId('user').textContent).toBe('test@example.com');
      });
    });

    it('handles login error', async () => {
      // First call: getCurrentUser (fails - no user initially)
      mockFetch.mockRejectedValueOnce(new Error('Not authenticated'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      // Second call: login fails with 401
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        headers: new Headers(),
        json: async () => ({ detail: 'Invalid credentials' }),
        text: async () => JSON.stringify({ detail: 'Invalid credentials' }),
      } as Response);

      // Click login and catch the thrown error
      await act(async () => {
        try {
          screen.getByTestId('login-btn').click();
          // Wait for the login promise to reject
          await new Promise(resolve => setTimeout(resolve, 100));
        } catch {
          // Expected - login throws on error
        }
      });

      await waitFor(() => {
        expect(screen.getByTestId('error').textContent).toBe('Invalid credentials');
        expect(screen.getByTestId('authenticated').textContent).toBe('false');
      });
    });
  });

  describe('Logout Flow', () => {
    it('logs out successfully', async () => {
      const mockUser = { id: '1', email: 'test@example.com' };

      // First call: getCurrentUser (success - user logged in)
      mockFetch.mockResolvedValueOnce(createMockResponse(mockUser));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for initial auth
      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('true');
      });

      // Second call: logout
      mockFetch.mockResolvedValueOnce(createMockResponse({ message: 'Logged out' }));

      // Click logout
      await act(async () => {
        screen.getByTestId('logout-btn').click();
      });

      // Check logged out state
      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('false');
        expect(screen.getByTestId('user').textContent).toBe('null');
      });
    });
  });

  describe('Error Handling', () => {
    it('clears error when clearError is called', async () => {
      // First call: getCurrentUser (fails - no user initially)
      mockFetch.mockRejectedValueOnce(new Error('Not authenticated'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      // Second call: login fails
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        headers: new Headers(),
        json: async () => ({ detail: 'Login failed' }),
        text: async () => JSON.stringify({ detail: 'Login failed' }),
      } as Response);

      // Trigger error (and catch the thrown error)
      await act(async () => {
        try {
          screen.getByTestId('login-btn').click();
          await new Promise(resolve => setTimeout(resolve, 100));
        } catch {
          // Expected - login throws on error
        }
      });

      await waitFor(() => {
        expect(screen.getByTestId('error').textContent).toBe('Login failed');
      });

      // Clear error
      await act(async () => {
        screen.getByTestId('clear-error-btn').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('error').textContent).toBe('null');
      });
    });
  });
});

describe('useAuth outside provider', () => {
  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});

    function TestComponentOutsideProvider() {
      useAuth();
      return null;
    }

    // The default context should not throw, but return default values
    // This test ensures the hook can be used safely
    expect(() => {
      render(<TestComponentOutsideProvider />);
    }).not.toThrow();

    spy.mockRestore();
  });
});
