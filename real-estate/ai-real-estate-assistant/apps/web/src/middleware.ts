import createMiddleware from 'next-intl/middleware';
import { NextResponse, type NextRequest } from 'next/server';
import { locales, defaultLocale } from './i18n/config';

/**
 * Next.js Middleware for i18n routing and authentication protection.
 *
 * This middleware:
 * 1. Handles locale detection and redirection
 * 2. Protects routes that require authentication
 *
 * Public routes (accessible without authentication):
 * - /{locale}/auth/* - Authentication pages
 * - /api/v1/auth/* - Auth API endpoints
 * - /_next/* - Next.js internals
 * - /static/* - Static files
 * - /favicon.ico - Favicon
 *
 * Protected routes (require authentication):
 * - All other routes under /{locale}/*
 */

// Create the next-intl middleware
const intlMiddleware = createMiddleware({
  locales,
  defaultLocale,
  localePrefix: 'always', // Always show locale prefix: /pl/search, /en/search
});

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Handle API routes separately (no i18n)
  if (pathname.startsWith('/api/')) {
    return NextResponse.next();
  }

  // Handle static files and Next.js internals
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/static/') ||
    pathname === '/favicon.ico'
  ) {
    return NextResponse.next();
  }

  // First, handle i18n routing
  const intlResponse = intlMiddleware(request);

  // Extract locale from pathname or use default
  const pathSegments = pathname.split('/').filter(Boolean);
  const localeFromPath = pathSegments[0];
  const hasLocalePrefix = locales.includes(localeFromPath as typeof locales[number]);
  const currentLocale = hasLocalePrefix ? localeFromPath : defaultLocale;

  // Get the path without locale prefix for route checking
  const pathWithoutLocale = hasLocalePrefix
    ? '/' + pathSegments.slice(1).join('/')
    : pathname;

  // Check if this is a public route (auth pages)
  const isAuthRoute =
    pathWithoutLocale.startsWith('/auth/') ||
    pathWithoutLocale === '/auth';

  if (isAuthRoute) {
    return intlResponse;
  }

  // If the intl middleware returned a redirect (for locale handling), return it
  if (intlResponse.status === 307 || intlResponse.status === 308) {
    // But still check auth for the redirect destination
    const location = intlResponse.headers.get('location');
    if (location) {
      const redirectUrl = new URL(location);
      const redirectPath = redirectUrl.pathname;

      // Extract locale from redirect path
      const redirectSegments = redirectPath.split('/').filter(Boolean);
      const redirectLocale = redirectSegments[0];
      const redirectPathWithoutLocale = locales.includes(redirectLocale as typeof locales[number])
        ? '/' + redirectSegments.slice(1).join('/')
        : redirectPath;

      // Check if redirecting to auth route
      if (redirectPathWithoutLocale.startsWith('/auth/') || redirectPathWithoutLocale === '/auth') {
        return intlResponse;
      }
    }
    // For non-auth redirects, continue with auth check
  }

  // Check for access_token cookie (set by backend auth)
  const accessToken = request.cookies.get('access_token')?.value;

  if (!accessToken) {
    // No access token found, redirect to login with locale
    const loginUrl = new URL(`/${currentLocale}/auth/login`, request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Token exists, return the intl response (or continue)
  return intlResponse;
}

/**
 * Configure which routes the middleware should run on.
 *
 * Matches all request paths except:
 * - api routes (handled by backend)
 * - _next/static (static files)
 * - _next/image (image optimization files)
 * - favicon.ico (favicon file)
 * - static files
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api routes that don't need middleware (handled by backend)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - static files
     */
    '/((?!api/|_next/static|_next/image|favicon.ico|static|.*\\..*).*)',
  ],
};
