'use client';

/**
 * Push Notification Utilities
 * Handles Web Push API subscription and notification management
 *
 * Note: This is frontend-only. Backend endpoints for VAPID keys and
 * subscription storage need to be implemented separately.
 */

/**
 * Convert a base64 string to Uint8Array for VAPID key
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Check if push notifications are supported
 */
export function isPushSupported(): boolean {
  if (typeof window === 'undefined') return false;
  return 'PushManager' in window && 'serviceWorker' in navigator;
}

/**
 * Check the current notification permission status
 */
export function getNotificationPermission(): NotificationPermission {
  if (typeof window === 'undefined') return 'default';
  return Notification.permission;
}

/**
 * Check if notifications are enabled (granted permission)
 */
export function areNotificationsEnabled(): boolean {
  return getNotificationPermission() === 'granted';
}

/**
 * Request notification permission from the user
 * Returns the permission status after the request
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!isPushSupported()) {
    console.warn('[Push] Push notifications are not supported');
    return 'denied';
  }

  try {
    const permission = await Notification.requestPermission();
    console.log('[Push] Permission status:', permission);
    return permission;
  } catch (error) {
    console.error('[Push] Error requesting permission:', error);
    return 'denied';
  }
}

/**
 * Get the current push subscription
 * Returns null if not subscribed or not supported
 */
export async function getPushSubscription(): Promise<PushSubscription | null> {
  if (!isPushSupported()) return null;

  try {
    const registration = await navigator.serviceWorker.ready;
    return registration.pushManager.getSubscription();
  } catch (error) {
    console.error('[Push] Error getting subscription:', error);
    return null;
  }
}

/**
 * Check if the user is currently subscribed to push notifications
 */
export async function isSubscribedToPush(): Promise<boolean> {
  const subscription = await getPushSubscription();
  return subscription !== null;
}

/**
 * Subscribe to push notifications
 * Requires a VAPID public key from the backend
 *
 * @param vapidPublicKey - The VAPID public key from the server
 * @returns The push subscription object or null on failure
 */
export async function subscribeToPush(vapidPublicKey: string): Promise<PushSubscription | null> {
  if (!isPushSupported()) {
    console.warn('[Push] Push notifications are not supported');
    return null;
  }

  // Request permission first
  const permission = await requestNotificationPermission();
  if (permission !== 'granted') {
    console.warn('[Push] Notification permission not granted');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;

    // Check for existing subscription
    const existingSubscription = await registration.pushManager.getSubscription();
    if (existingSubscription) {
      console.log('[Push] Already subscribed');
      return existingSubscription;
    }

    // Create new subscription
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey) as unknown as BufferSource,
    });

    console.log('[Push] Successfully subscribed');
    return subscription;
  } catch (error) {
    console.error('[Push] Error subscribing:', error);
    return null;
  }
}

/**
 * Unsubscribe from push notifications
 * Returns true if successfully unsubscribed
 */
export async function unsubscribeFromPush(): Promise<boolean> {
  const subscription = await getPushSubscription();

  if (!subscription) {
    console.log('[Push] No active subscription to unsubscribe');
    return true;
  }

  try {
    const success = await subscription.unsubscribe();
    if (success) {
      console.log('[Push] Successfully unsubscribed');
    }
    return success;
  } catch (error) {
    console.error('[Push] Error unsubscribing:', error);
    return false;
  }
}

/**
 * Get subscription details for sending to the backend
 * Returns the subscription as a JSON object
 */
export async function getSubscriptionDetails(): Promise<{
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
} | null> {
  const subscription = await getPushSubscription();

  if (!subscription) return null;

  const keys = subscription.getKey('p256dh');
  const auth = subscription.getKey('auth');

  if (!keys || !auth) return null;

  return {
    endpoint: subscription.endpoint,
    keys: {
      p256dh: btoa(String.fromCharCode(...new Uint8Array(keys))),
      auth: btoa(String.fromCharCode(...new Uint8Array(auth))),
    },
  };
}

/**
 * Show a local notification (for testing or non-push notifications)
 */
export async function showLocalNotification(
  title: string,
  options?: NotificationOptions
): Promise<void> {
  if (!isPushSupported()) return;

  const permission = getNotificationPermission();
  if (permission !== 'granted') {
    console.warn('[Push] No permission to show notifications');
    return;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    await registration.showNotification(title, {
      icon: '/icon-192x192.png',
      badge: '/icon-192x192.png',
      ...options,
    });
  } catch (error) {
    console.error('[Push] Error showing notification:', error);
  }
}
