'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';

import { ApiError } from '@/lib/api';
import * as authApi from '@/lib/auth';
import type { User } from '@/lib/auth';

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

// Default context value for SSR/SSG when AuthProvider is not wrapping the component
const defaultAuthContext: AuthContextType = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,
  login: async () => {
    throw new Error('AuthProvider not found');
  },
  register: async () => {
    throw new Error('AuthProvider not found');
  },
  logout: async () => {
    throw new Error('AuthProvider not found');
  },
  refreshUser: async () => {
    // Silent no-op during SSR
  },
  clearError: () => {},
};

const AuthContext = createContext<AuthContextType>(defaultAuthContext);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch current user on mount
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        // User is not authenticated or token expired
        if (err instanceof ApiError) {
          // Don't set error for 401 - just means not logged in
          if (err.status !== 401) {
            setError(err.message);
          }
        } else {
          setError('Failed to fetch user');
        }
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await authApi.login(email, password);
      setUser(response.user);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, fullName?: string) => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await authApi.register(email, password, fullName);
      setUser(response.user);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setError(null);
    setIsLoading(true);

    try {
      await authApi.logout();
      setUser(null);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Logout failed';
      setError(message);
      // Still clear user on error
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await authApi.getCurrentUser();
      setUser(currentUser);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        // Token expired, clear user
        setUser(null);
      }
      setError(err instanceof Error ? err.message : 'Failed to refresh user');
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    error,
    login,
    register,
    logout,
    refreshUser,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access the auth context.
 *
 * Returns default values when used outside of AuthProvider (e.g., during SSR).
 */
export function useAuth(): AuthContextType {
  return useContext(AuthContext);
}
