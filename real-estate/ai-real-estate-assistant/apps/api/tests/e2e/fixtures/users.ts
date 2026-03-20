/**
 * Test user fixtures for E2E tests.
 * Provides predefined test users with different roles and states.
 */

export interface TestUser {
  id: string;
  email: string;
  password: string;
  fullName: string;
  role: 'user' | 'agent' | 'admin';
  isVerified: boolean;
}

/**
 * Predefined test users for different scenarios.
 * Use these in tests instead of creating random users.
 */
export const TEST_USERS: Record<string, TestUser> = {
  /**
   * Basic verified user for standard tests.
   */
  basic: {
    id: 'test-user-basic-001',
    email: 'test-basic@example.com',
    password: 'TestPassword123!',
    fullName: 'Basic Test User',
    role: 'user',
    isVerified: true,
  },

  /**
   * Admin user for admin-only features.
   */
  admin: {
    id: 'test-user-admin-001',
    email: 'test-admin@example.com',
    password: 'AdminPassword123!',
    fullName: 'Admin Test User',
    role: 'admin',
    isVerified: true,
  },

  /**
   * Agent user for lead management tests.
   */
  agent: {
    id: 'test-user-agent-001',
    email: 'test-agent@example.com',
    password: 'AgentPassword123!',
    fullName: 'Agent Test User',
    role: 'agent',
    isVerified: true,
  },

  /**
   * Unverified user for email verification tests.
   */
  unverified: {
    id: 'test-user-unverified-001',
    email: 'test-unverified@example.com',
    password: 'TestPassword123!',
    fullName: 'Unverified User',
    role: 'user',
    isVerified: false,
  },
};

/**
 * Get a test user by key.
 */
export function getTestUser(key: keyof typeof TEST_USERS = 'basic'): TestUser {
  return TEST_USERS[key];
}

/**
 * Get all test users.
 */
export function getAllTestUsers(): TestUser[] {
  return Object.values(TEST_USERS);
}

/**
 * Generate a unique email for registration tests.
 * Uses timestamp to ensure uniqueness.
 */
export function generateUniqueEmail(): string {
  const timestamp = Date.now();
  return `test-${timestamp}@example.com`;
}
