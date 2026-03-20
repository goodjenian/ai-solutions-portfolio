'use client';

import { useState, useEffect } from 'react';
import { RefreshCw, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface UpdateBannerProps {
  className?: string;
}

/**
 * Update Banner Component
 * Shows when a new version of the service worker is available
 */
export function UpdateBanner({ className }: UpdateBannerProps) {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const handleUpdateAvailable = () => {
      setShowBanner(true);
    };

    window.addEventListener('sw-update-available', handleUpdateAvailable);

    return () => {
      window.removeEventListener('sw-update-available', handleUpdateAvailable);
    };
  }, []);

  const handleUpdate = () => {
    window.location.reload();
  };

  const handleDismiss = () => {
    setShowBanner(false);
  };

  if (!showBanner) {
    return null;
  }

  return (
    <div
      className={cn(
        'fixed top-0 left-0 right-0 z-50 bg-blue-600 px-4 py-2 text-center text-sm text-white transition-all',
        className
      )}
    >
      <div className="flex items-center justify-center gap-3">
        <RefreshCw className="h-4 w-4" />
        <span>A new version is available. Refresh to update.</span>
        <Button variant="secondary" size="sm" onClick={handleUpdate} className="ml-2">
          Refresh
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDismiss}
          className="text-white hover:text-white"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
