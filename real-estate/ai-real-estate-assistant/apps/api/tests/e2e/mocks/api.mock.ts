/**
 * API response mocks for E2E tests.
 * Provides mock handlers for search, auth, and other API endpoints.
 */

import { Route } from '@playwright/test';
import { TEST_PROPERTIES } from '../fixtures/properties';
import { TEST_USERS } from '../fixtures/users';

/**
 * Mock search API response with properties.
 */
export async function mockSearchSuccess(route: Route): Promise<void> {
  await route.fulfill({
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Expose-Headers': 'X-Request-ID',
      'X-Request-ID': 'req-mock-search-success',
    },
    body: JSON.stringify({
      properties: TEST_PROPERTIES,
      total: TEST_PROPERTIES.length,
      page: 1,
      page_size: 20,
    }),
  });
}

/**
 * Mock empty search results.
 */
export async function mockSearchEmpty(route: Route): Promise<void> {
  await route.fulfill({
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'X-Request-ID': 'req-mock-search-empty',
    },
    body: JSON.stringify({
      properties: [],
      total: 0,
      page: 1,
      page_size: 20,
    }),
  });
}

/**
 * Mock search API error.
 */
export async function mockSearchError(
  route: Route,
  statusCode: number = 500,
  message: string = 'Search failed'
): Promise<void> {
  await route.fulfill({
    status: statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'X-Request-ID': `req-mock-search-error-${statusCode}`,
    },
    body: JSON.stringify({ detail: message }),
  });
}

/**
 * Mock successful registration.
 */
export async function mockRegisterSuccess(route: Route): Promise<void> {
  await route.fulfill({
    status: 201,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Set-Cookie': 'access_token=mock-access-token; Path=/; HttpOnly',
    },
    body: JSON.stringify({
      user: {
        id: 'new-user-001',
        email: 'newuser@example.com',
        full_name: 'New User',
        role: 'user',
        is_verified: false,
      },
      message: 'Registration successful. Please check your email to verify your account.',
    }),
  });
}

/**
 * Mock successful login.
 * Returns AuthResponse format expected by frontend.
 */
export async function mockLoginSuccess(route: Route): Promise<void> {
  const testUser = TEST_USERS.basic;

  await route.fulfill({
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Set-Cookie': [
        'access_token=mock-access-token; Path=/; HttpOnly; SameSite=Lax',
        'refresh_token=mock-refresh-token; Path=/; HttpOnly; SameSite=Lax',
      ].join(', '),
    },
    body: JSON.stringify({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: testUser.id,
        email: testUser.email,
        full_name: testUser.fullName,
        role: testUser.role,
        is_active: true,
        is_verified: testUser.isVerified,
        created_at: new Date().toISOString(),
      },
    }),
  });
}

/**
 * Mock failed login (invalid credentials).
 */
export async function mockLoginError(route: Route): Promise<void> {
  await route.fulfill({
    status: 401,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
    body: JSON.stringify({
      detail: 'Invalid email or password',
    }),
  });
}

/**
 * Mock successful logout.
 */
export async function mockLogoutSuccess(route: Route): Promise<void> {
  await route.fulfill({
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Set-Cookie': [
        'access_token=; Path=/; Max-Age=0',
        'refresh_token=; Path=/; Max-Age=0',
      ].join(', '),
    },
    body: JSON.stringify({ message: 'Logged out successfully' }),
  });
}

/**
 * Mock get current user (authenticated).
 */
export async function mockGetCurrentUser(route: Route): Promise<void> {
  const testUser = TEST_USERS.basic;

  await route.fulfill({
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
    body: JSON.stringify({
      id: testUser.id,
      email: testUser.email,
      full_name: testUser.fullName,
      role: testUser.role,
      is_verified: testUser.isVerified,
    }),
  });
}

/**
 * Mock unauthorized (not logged in).
 */
export async function mockUnauthorized(route: Route): Promise<void> {
  await route.fulfill({
    status: 401,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
    body: JSON.stringify({ detail: 'Not authenticated' }),
  });
}

/**
 * Setup all auth-related mocks for a page.
 */
export function setupAuthMocks(page: import('@playwright/test').Page): void {
  // Mock login
  page.route('**/api/v1/auth/login', async (route) => {
    const request = route.request();
    if (request.method() === 'OPTIONS') {
      await route.fulfill({ status: 204, headers: { 'Access-Control-Allow-Origin': '*' } });
      return;
    }
    await mockLoginSuccess(route);
  });

  // Mock logout
  page.route('**/api/v1/auth/logout', async (route) => {
    const request = route.request();
    if (request.method() === 'OPTIONS') {
      await route.fulfill({ status: 204, headers: { 'Access-Control-Allow-Origin': '*' } });
      return;
    }
    await mockLogoutSuccess(route);
  });

  // Mock get current user
  page.route('**/api/v1/auth/me', async (route) => {
    const request = route.request();
    if (request.method() === 'OPTIONS') {
      await route.fulfill({ status: 204, headers: { 'Access-Control-Allow-Origin': '*' } });
      return;
    }
    await mockGetCurrentUser(route);
  });
}
