'use client';

import React from 'react';
import { Clock, Car, Bike, Footprints, Train } from 'lucide-react';
import { cn } from '@/lib/utils';
import { type CommuteMode } from '@/lib/types';

export interface CommuteBadgeProps {
  /** Duration in seconds */
  duration: number;
  /** Transport mode */
  mode?: CommuteMode;
  /** Optional: additional CSS classes */
  className?: string;
  /** Optional: whether to show the mode icon */
  showIcon?: boolean;
}

/**
 * CommuteTimeBadge - Displays commute time as a small badge on property cards
 * Shows the time and transport mode for a single destination.
 *
 * Usage:
 * <CommuteBadge duration={1800} mode="transit" />
 */
export function CommuteBadge({
  duration,
  mode = 'transit',
  className = '',
  showIcon = true,
}: CommuteBadgeProps): React.ReactElement | null {
  if (duration < 0) return null;

  // Format duration to human-readable string
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.round((seconds % 3600) / 60);
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
    }
  };

  // Get color based on duration (green = quick, red = long)
  const getColorClass = (seconds: number): string => {
    if (seconds < 900) { // < 15 min
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
    } else if (seconds < 1800) { // < 30 min
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
    } else if (seconds < 3600) { // < 60 min
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-300';
    }
    return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
  };

  // Get icon based on transport mode
  const getIcon = (m: CommuteMode) => {
    switch (m) {
      case 'driving':
        return <Car className="h-3 w-3" />;
      case 'walking':
        return <Footprints className="h-3 w-3" />;
      case 'bicycling':
        return <Bike className="h-3 w-3" />;
      case 'transit':
        return <Train className="h-3 w-3" />;
      default:
        return <Clock className="h-3 w-3" />;
    }
  };

  return (
    <div className={cn(
      'inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium',
      getColorClass(duration),
      className
    )}>
      {showIcon && getIcon(mode)}
      <span>{formatDuration(duration)}</span>
    </div>
  );
}
