'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { UserMenu } from '@/components/auth/UserMenu';
import { LanguageSwitcher } from '@/components/ui/language-switcher';
import {
  BarChart3,
  BookOpen,
  Building2,
  FileText,
  Heart,
  MessageSquare,
  Moon,
  Search,
  Settings,
  Sun,
  Globe,
  Users,
} from 'lucide-react';

const THEME_STORAGE_KEY = 'theme';

export function MainNav() {
  const pathname = usePathname();
  const locale = useLocale();
  const t = useTranslations('nav');
  const tCommon = useTranslations('common');

  const routes = [
    {
      href: '/',
      label: t('home'),
      icon: Building2,
    },
    {
      href: '/search',
      label: t('search'),
      icon: Search,
    },
    {
      href: '/favorites',
      label: t('favorites'),
      icon: Heart,
    },
    {
      href: '/documents',
      label: t('documents'),
      icon: FileText,
    },
    {
      href: '/city-overview',
      label: t('cities'),
      icon: Globe,
    },
    {
      href: '/chat',
      label: t('assistant'),
      icon: MessageSquare,
    },
    {
      href: '/analytics',
      label: t('analytics'),
      icon: BarChart3,
    },
    {
      href: '/agents',
      label: t('agents'),
      icon: Users,
    },
    {
      href: '/knowledge',
      label: t('knowledge'),
      icon: BookOpen,
    },
    {
      href: '/settings',
      label: t('settings'),
      icon: Settings,
    },
  ];

  // Check if a route is active by comparing the pathname without locale prefix
  const isActiveRoute = (href: string) => {
    // Remove locale prefix from pathname for comparison
    const pathWithoutLocale = pathname.replace(/^\/(pl|en|ru)/, '') || '/';
    return pathWithoutLocale === href || (href !== '/' && pathWithoutLocale.startsWith(href));
  };

  const toggleTheme = () => {
    const isDark = document.documentElement.classList.contains('dark');
    const next = isDark ? 'light' : 'dark';
    window.localStorage.setItem(THEME_STORAGE_KEY, next);
    document.documentElement.classList.toggle('dark', !isDark);
  };

  return (
    <nav className="flex items-center justify-center space-x-6 lg:space-x-8">
      {/* Logo - absolutely positioned on the left */}
      <div className="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-xl hidden md:block">
        AI Estate
      </div>

      {routes.map((route) => (
        <Link
          key={route.href}
          href={`/${locale}${route.href}`}
          className={cn(
            'text-sm font-medium transition-colors hover:text-primary flex items-center gap-x-2',
            isActiveRoute(route.href) ? 'text-foreground' : 'text-muted-foreground'
          )}
        >
          <route.icon className="w-4 h-4" />
          {route.label}
        </Link>
      ))}
      <div className="ml-auto flex items-center gap-2">
        <LanguageSwitcher />
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={tCommon('toggleTheme')}
        >
          <Sun className="h-4 w-4 hidden dark:block" />
          <Moon className="h-4 w-4 block dark:hidden" />
        </Button>
        <UserMenu />
      </div>
    </nav>
  );
}
