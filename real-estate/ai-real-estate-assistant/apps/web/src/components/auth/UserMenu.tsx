'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useLocale, useTranslations } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { LogOut, User, Settings, ChevronDown } from 'lucide-react';

/**
 * User menu component that shows user info and logout option.
 * Displays when user is authenticated, shows login/register buttons when not.
 */
export function UserMenu() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const locale = useLocale();
  const t = useTranslations('auth');

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-8 w-20 bg-muted animate-pulse rounded" />
      </div>
    );
  }

  // Not authenticated - show login/register buttons
  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center gap-2">
        <Link href={`/${locale}/auth/login`}>
          <Button variant="ghost" size="sm">
            {t('signIn')}
          </Button>
        </Link>
        <Link href={`/${locale}/auth/register`}>
          <Button size="sm">{t('signUp')}</Button>
        </Link>
      </div>
    );
  }

  // Authenticated - show user menu
  const initials = user.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : user.email.slice(0, 2).toUpperCase();

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-full px-3 py-1.5 hover:bg-accent transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div className="flex items-center justify-center h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-medium">
          {initials}
        </div>
        <span className="hidden sm:block text-sm font-medium max-w-[100px] truncate">
          {user.full_name || user.email.split('@')[0]}
        </span>
        <ChevronDown className="h-4 w-4 text-muted-foreground" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-md border bg-popover shadow-lg z-50">
          <div className="p-3 border-b">
            <p className="text-sm font-medium">{user.full_name || t('user')}</p>
            <p className="text-xs text-muted-foreground truncate">{user.email}</p>
          </div>
          <div className="p-1">
            <Link
              href={`/${locale}/profile`}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-sm hover:bg-accent transition-colors"
            >
              <User className="h-4 w-4" />
              {t('profile')}
            </Link>
            <Link
              href={`/${locale}/settings`}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-sm hover:bg-accent transition-colors"
            >
              <Settings className="h-4 w-4" />
              {t('settings')}
            </Link>
          </div>
          <div className="p-1 border-t">
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-sm hover:bg-accent transition-colors text-destructive"
            >
              <LogOut className="h-4 w-4" />
              {t('signOut')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
