import type { NextConfig } from 'next';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import createNextIntlPlugin from 'next-intl/plugin';
import withPWAInit from '@ducanh2912/next-pwa';

const configDir = dirname(fileURLToPath(import.meta.url));
const turbopackRoot = resolve(configDir, '..', '..');

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

// PWA configuration - simplified for v10.2.9
const withPWA = withPWAInit({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  register: true,
});

const nextConfig: NextConfig = {
  output: 'standalone',
  turbopack: {
    root: turbopackRoot,
  },
  async headers() {
    const isProduction = process.env.NODE_ENV === 'production';

    // Content Security Policy
    // Development: More permissive for hot reload and inline scripts
    // Production: Strict policy allowing only trusted sources
    const cspDirectives = isProduction
      ? {
          'default-src': ["'self'"],
          'script-src': ["'self'"],
          'style-src': ["'self'", "'unsafe-inline'"],
          'img-src': ["'self'", 'data:', 'https:', 'blob:'],
          'font-src': ["'self'", 'data:'],
          'connect-src': [
            "'self'",
            process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
            'https://*.vercel.app',
            // Push notification services
            'https://fcm.googleapis.com',
            'https://updates.push.services.mozilla.com',
            'https://*.push.apple.com',
          ],
          'frame-src': ["'none'"],
          'object-src': ["'none'"],
          'base-uri': ["'self'"],
          'form-action': ["'self'"],
          'frame-ancestors': ["'none'"],
          'upgrade-insecure-requests': [],
        }
      : {
          'default-src': ["'self'"],
          'script-src': ["'self'", "'unsafe-eval'", "'unsafe-inline'"],
          'style-src': ["'self'", "'unsafe-inline'"],
          'img-src': ["'self'", 'data:', 'https:', 'blob:', 'http://localhost:*'],
          'font-src': ["'self'", 'data:'],
          'connect-src': [
            "'self'",
            'http://localhost:*',
            'ws://localhost:*',
            'https://localhost:*',
          ],
          'frame-src': ["'none'"],
          'object-src': ["'none'"],
        };

    const cspHeaderValue = Object.entries(cspDirectives)
      .map(([directive, values]) => `${directive} ${values.join(' ')}`)
      .join('; ');

    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value:
              'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()',
          },
          {
            key: 'Content-Security-Policy',
            value: cspHeaderValue,
          },
          // HSTS only in production when using HTTPS
          ...(isProduction
            ? [
                {
                  key: 'Strict-Transport-Security',
                  value: 'max-age=31536000; includeSubDomains; preload',
                },
              ]
            : []),
        ],
      },
    ];
  },
};

export default withPWA(withNextIntl(nextConfig));
