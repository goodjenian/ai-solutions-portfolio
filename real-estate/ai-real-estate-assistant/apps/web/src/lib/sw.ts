'use client';

/**
 * Service Worker Registration and Management Utilities
 * Handles PWA installation and service worker lifecycle
 */

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

let deferredInstallPrompt: BeforeInstallPromptEvent | null = null;

/**
 * Register the service worker
 * Should be called once when the app loads
 */
export function registerServiceWorker(): void {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });

      console.log('[SW] Service Worker registered with scope:', registration.scope);

      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New content is available, notify the user
              console.log('[SW] New content available, please refresh.');
              window.dispatchEvent(new CustomEvent('sw-update-available'));
            }
          });
        }
      });
    } catch (error) {
      console.error('[SW] Service Worker registration failed:', error);
    }
  });

  // Listen for the beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e as BeforeInstallPromptEvent;
    window.dispatchEvent(new CustomEvent('pwa-install-available'));
  });

  // Listen for successful installation
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');
    deferredInstallPrompt = null;
    window.dispatchEvent(new CustomEvent('pwa-installed'));
  });
}

/**
 * Check if the app can be installed (PWA install prompt is available)
 */
export function canInstallPWA(): boolean {
  return deferredInstallPrompt !== null;
}

/**
 * Trigger the PWA install prompt
 * Returns true if the user accepted, false if dismissed
 */
export async function promptPWAInstall(): Promise<boolean> {
  if (!deferredInstallPrompt) {
    console.warn('[PWA] Install prompt not available');
    return false;
  }

  try {
    await deferredInstallPrompt.prompt();
    const { outcome } = await deferredInstallPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('[PWA] User accepted the install prompt');
      return true;
    } else {
      console.log('[PWA] User dismissed the install prompt');
      return false;
    }
  } catch (error) {
    console.error('[PWA] Error showing install prompt:', error);
    return false;
  } finally {
    deferredInstallPrompt = null;
  }
}

/**
 * Check if the app is running as a standalone PWA
 */
export function isStandalonePWA(): boolean {
  if (typeof window === 'undefined') return false;

  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

/**
 * Check if the service worker is currently controlling the page
 */
export function isServiceWorkerActive(): boolean {
  if (typeof navigator === 'undefined') return false;
  return !!navigator.serviceWorker?.controller;
}

/**
 * Get the current service worker registration
 */
export async function getServiceWorkerRegistration(): Promise<ServiceWorkerRegistration | null> {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
    return null;
  }

  const registration = await navigator.serviceWorker.getRegistration();
  return registration ?? null;
}

/**
 * Unregister the service worker (useful for debugging or cleanup)
 */
export async function unregisterServiceWorker(): Promise<boolean> {
  const registration = await getServiceWorkerRegistration();
  if (registration) {
    const success = await registration.unregister();
    if (success) {
      console.log('[SW] Service Worker unregistered');
    }
    return success;
  }
  return false;
}
