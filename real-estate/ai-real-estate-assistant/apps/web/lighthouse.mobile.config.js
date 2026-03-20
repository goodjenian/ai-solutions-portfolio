import desktopConfig from './lighthouse.config.js';

module.exports = {
  ...desktopConfig,
  settings: {
    ...desktopConfig.settings,
    // Mobile configuration
    screenEmulation: {
      mobile: true,
      width: 375,
      height: 667,
      deviceScaleFactor: 2.6,
      disabled: false,
    },

    // Mobile throttling (simulates 4G)
    throttling: {
      rttMs: 150,
      throughputKbps: 1638,
      cpuSlowdownMultiplier: 4,
    },
  },

  // Mobile-specific assertions (slightly relaxed)
  assertions: {
    // Performance score can be slightly lower on mobile
    'categories:performance': ['error', { minScore: 0.85 }],

    // Accessibility score must be 90+
    'categories:accessibility': ['error', { minScore: 0.9 }],

    // Best practices score must be 90+
    'categories:best-practices': ['error', { minScore: 0.9 }],

    // SEO score must be 80+
    'categories:seo': ['warn', { minScore: 0.8 }],

    // Core Web Vitals (mobile-specific thresholds)
    'first-contentful-paint': ['error', { maxNumericValue: 3000 }],
    'largest-contentful-paint': ['error', { maxNumericValue: 4000 }],
    'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
    'total-blocking-time': ['error', { maxNumericValue: 600 }],
    'speed-index': ['error', { maxNumericValue: 4000 }],

    // Resource timing (relaxed for mobile)
    'server-response-time': ['error', { maxNumericValue: 1000 }],
    interactive: ['error', { maxNumericValue: 5000 }],

    // Mobile-specific checks
    viewport: 'error',
    'font-size': 'error',
    'tap-targets': 'error',

    // Accessibility checks
    'color-contrast': 'error',
    'document-title': 'error',
    'html-has-lang': 'error',
    'image-alt': 'error',
    label: 'error',
    'link-name': 'error',
    'meta-viewport': 'error',

    // Best practices
    'no-vulnerable-libraries': 'error',
    'is-on-https': 'error',
  },
};
