'use client';

import React, { useState } from 'react';
import { Heart, Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';
import { useFavorites } from '@/contexts/FavoritesContext';
import { useAuth } from '@/contexts/AuthContext';

interface HeartButtonProps {
  propertyId: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showTooltip?: boolean;
  onToggle?: (isFavorited: boolean) => void;
}

export function HeartButton({
  propertyId,
  className,
  size = 'md',
  showTooltip = true,
  onToggle,
}: HeartButtonProps) {
  const { isAuthenticated } = useAuth();
  const { isFavorited, toggleFavorite } = useFavorites();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const favorited = isFavorited(propertyId);

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  const handleClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      setError('Please log in to favorite properties');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const newState = await toggleFavorite(propertyId);
      onToggle?.(newState);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update favorite');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isLoading}
      className={cn(
        'relative rounded-full p-2 transition-all duration-200',
        'hover:bg-gray-100 dark:hover:bg-gray-800',
        'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      title={showTooltip ? (favorited ? 'Remove from favorites' : 'Add to favorites') : undefined}
      aria-label={favorited ? 'Remove from favorites' : 'Add to favorites'}
      aria-pressed={favorited}
    >
      {isLoading ? (
        <Loader2 className={cn(sizeClasses[size], 'animate-spin text-gray-400')} />
      ) : (
        <Heart
          className={cn(
            sizeClasses[size],
            'transition-colors duration-200',
            favorited ? 'fill-red-500 text-red-500' : 'text-gray-400 hover:text-red-400'
          )}
        />
      )}

      {error && (
        <span className="sr-only" role="alert">
          {error}
        </span>
      )}
    </button>
  );
}
