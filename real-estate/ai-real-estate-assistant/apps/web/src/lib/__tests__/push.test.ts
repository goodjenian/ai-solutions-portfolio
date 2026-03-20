/**
 * Tests for Push Notification Utilities.
 *
 * Task #58: Comprehensive Test Suite Update
 *
 * Note: These tests verify utility functions handle browser environments.
 * We test the functions that are exported and work with the test environment.
 */

// Mock Notification API before importing the module
class MockNotification {
  static permission: NotificationPermission = 'default';
  static requestPermission = jest.fn().mockResolvedValue('default');

  constructor(_title: string, _options?: NotificationOptions) {
    // Mock implementation
  }
}

// Set up global Notification mock
Object.defineProperty(global, 'Notification', {
  value: MockNotification,
  writable: true,
  configurable: true,
});

// Mock PushManager in window to make isPushSupported return true
Object.defineProperty(window, 'PushManager', {
  value: jest.fn(),
  writable: true,
  configurable: true,
});

import {
  isPushSupported,
  getNotificationPermission,
  areNotificationsEnabled,
  requestNotificationPermission,
} from '../push';

describe('Push Utilities', () => {
  // Store original serviceWorker for proper restoration
  const originalServiceWorker = navigator.serviceWorker;

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset permission to default
    MockNotification.permission = 'default';
    MockNotification.requestPermission = jest.fn().mockResolvedValue('default');
    // Ensure PushManager is available
    Object.defineProperty(window, 'PushManager', {
      value: jest.fn(),
      writable: true,
      configurable: true,
    });
    // Ensure serviceWorker is available in navigator
    Object.defineProperty(navigator, 'serviceWorker', {
      value: originalServiceWorker || {},
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    // Restore serviceWorker after each test
    Object.defineProperty(navigator, 'serviceWorker', {
      value: originalServiceWorker,
      writable: true,
      configurable: true,
    });
  });

  describe('isPushSupported', () => {
    it('returns true when PushManager and serviceWorker are available', () => {
      const result = isPushSupported();
      expect(result).toBe(true);
    });

    it('returns false when PushManager is not available', () => {
      const originalPushManager = (window as unknown as Record<string, unknown>).PushManager;

      // @ts-expect-error - removing PushManager for test
      delete (window as unknown as Record<string, unknown>).PushManager;

      const result = isPushSupported();

      expect(result).toBe(false);

      // Restore
      if (originalPushManager) {
        Object.defineProperty(window, 'PushManager', {
          value: originalPushManager,
          writable: true,
          configurable: true,
        });
      }
    });

    it('returns false when serviceWorker is not in navigator', () => {
      const originalSW = navigator.serviceWorker;

      // Delete the property to make 'serviceWorker' in navigator return false
      // @ts-expect-error - removing serviceWorker for test
      delete (navigator as Record<string, unknown>).serviceWorker;

      const result = isPushSupported();

      expect(result).toBe(false);

      // Restore
      Object.defineProperty(navigator, 'serviceWorker', {
        value: originalSW,
        writable: true,
        configurable: true,
      });
    });
  });

  describe('getNotificationPermission', () => {
    it('returns default when permission is default', () => {
      MockNotification.permission = 'default';
      expect(getNotificationPermission()).toBe('default');
    });

    it('returns granted when permission is granted', () => {
      MockNotification.permission = 'granted';
      expect(getNotificationPermission()).toBe('granted');
    });

    it('returns denied when permission is denied', () => {
      MockNotification.permission = 'denied';
      expect(getNotificationPermission()).toBe('denied');
    });
  });

  describe('areNotificationsEnabled', () => {
    it('returns false when permission is default', () => {
      MockNotification.permission = 'default';
      expect(areNotificationsEnabled()).toBe(false);
    });

    it('returns true when permission is granted', () => {
      MockNotification.permission = 'granted';
      expect(areNotificationsEnabled()).toBe(true);
    });

    it('returns false when permission is denied', () => {
      MockNotification.permission = 'denied';
      expect(areNotificationsEnabled()).toBe(false);
    });
  });

  describe('requestNotificationPermission', () => {
    it('returns granted when user accepts', async () => {
      MockNotification.requestPermission = jest.fn().mockResolvedValue('granted');

      const result = await requestNotificationPermission();

      expect(result).toBe('granted');
      expect(MockNotification.requestPermission).toHaveBeenCalled();
    });

    it('returns denied when user denies', async () => {
      MockNotification.requestPermission = jest.fn().mockResolvedValue('denied');

      const result = await requestNotificationPermission();

      expect(result).toBe('denied');
    });

    it('returns default when user dismisses', async () => {
      MockNotification.requestPermission = jest.fn().mockResolvedValue('default');

      const result = await requestNotificationPermission();

      expect(result).toBe('default');
    });

    it('returns denied when push is not supported', async () => {
      const originalPushManager = (window as unknown as Record<string, unknown>).PushManager;

      // @ts-expect-error - removing PushManager for test
      delete (window as unknown as Record<string, unknown>).PushManager;

      const result = await requestNotificationPermission();

      expect(result).toBe('denied');

      // Restore
      Object.defineProperty(window, 'PushManager', {
        value: originalPushManager,
        writable: true,
        configurable: true,
      });
    });

    it('returns denied when requestPermission throws', async () => {
      MockNotification.requestPermission = jest.fn().mockRejectedValue(new Error('User dismissed'));

      const result = await requestNotificationPermission();

      expect(result).toBe('denied');
    });
  });
});

describe('Push Utilities Integration', () => {
  beforeEach(() => {
    // Ensure PushManager is available for integration tests
    Object.defineProperty(window, 'PushManager', {
      value: jest.fn(),
      writable: true,
      configurable: true,
    });
  });

  it('correctly relates permission and enabled status', () => {
    MockNotification.permission = 'granted';
    const permission = getNotificationPermission();
    const enabled = areNotificationsEnabled();

    expect(enabled).toBe(permission === 'granted');
    expect(enabled).toBe(true);
  });

  it('isPushSupported checks for required APIs', () => {
    const supported = isPushSupported();

    // Should return true with PushManager and serviceWorker
    expect(supported).toBe(true);
  });
});

describe('Push Utilities Error Handling', () => {
  beforeEach(() => {
    // Ensure PushManager is available
    Object.defineProperty(window, 'PushManager', {
      value: jest.fn(),
      writable: true,
      configurable: true,
    });
  });

  it('handles notification permission request gracefully', async () => {
    // Request permission should never throw
    const result = await requestNotificationPermission();

    // Should return a valid permission string
    expect(['granted', 'denied', 'default']).toContain(result);
  });

  it('getNotificationPermission never throws', () => {
    // This function should always return a valid permission
    expect(() => getNotificationPermission()).not.toThrow();
  });

  it('areNotificationsEnabled never throws', () => {
    expect(() => areNotificationsEnabled()).not.toThrow();
  });
});
