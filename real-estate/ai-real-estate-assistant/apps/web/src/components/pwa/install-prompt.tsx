'use client';

import { useState, useEffect, useCallback } from 'react';
import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface InstallPromptProps {
  className?: string;
}

/**
 * Install Prompt Component
 * Shows a prompt to install the PWA when the app is installable
 */
export function InstallPrompt({ className }: InstallPromptProps) {
  const [showPrompt, setShowPrompt] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia?.('(display-mode: standalone)')) {
      return;
    }

    // Check if prompt was dismissed before
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
      return;
    }

    // Listen for install availability
    const handleInstallAvailable = () => {
      setShowPrompt(true);
    };

    window.addEventListener('pwa-install-available', handleInstallAvailable);

    // Check if already available
    if ('BeforeInstallPromptEvent' in window) {
      setShowPrompt(true);
    }

    return () => {
      window.removeEventListener('pwa-install-available', handleInstallAvailable);
    };
  }, []);

  const handleInstall = useCallback(async () => {
    setIsInstalling(true);
    try {
      const { promptPWAInstall } = await import('@/lib/sw');
      const accepted = await promptPWAInstall();
      if (accepted) {
        setShowPrompt(false);
      }
    } catch (error) {
      console.error('Install failed:', error);
    } finally {
      setIsInstalling(false);
    }
  }, []);

  const handleLater = useCallback(() => {
    setShowPrompt(false);
  }, []);

  if (!showPrompt) {
    return null;
  }

  return (
    <Card className={`fixed bottom-4 left-4 right-4 z-50 mx-4 shadow-lg ${className || ''}`}>
      <div className="flex items-start gap-3 p-4">
        <div className="flex-shrink-0">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <Download className="h-5 w-5 text-primary" />
          </div>
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-foreground">Install App</p>
          <p className="text-xs text-muted">
            Install this app on your device for quick access and offline support.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleLater} className="text-muted">
            Later
          </Button>
          <Button size="sm" onClick={handleInstall} disabled={isInstalling}>
            {isInstalling ? 'Installing...' : 'Install'}
          </Button>
        </div>
      </div>
    </Card>
  );
}
