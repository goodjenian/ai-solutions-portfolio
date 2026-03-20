/** @type {import('lighthouse').Config} */
module.exports = {
  extends: 'lighthouse:default',
  settings: {
    // Performance thresholds for CI
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],

    // Skip audits that are not applicable
    skipAudits: [
      'uses-http2', // Dev server may not use HTTP/2
      'uses-rel-preconnect', // Often not applicable in dev
      'unused-javascript', // Development builds have more code
      'unused-css-rules', // Development builds have more styles
    ],

    // Desktop configuration (also test mobile separately)
    screenEmulation: {
      mobile: false,
      width: 1350,
      height: 940,
      deviceScaleFactor: 1,
      disabled: false,
    },

    // Throttling configuration (simulates slow network)
    throttling: {
      rttMs: 40,
      throughputKbps: 10240,
      cpuSlowdownMultiplier: 1,
    },
  },

  // Custom assertions for CI
  assertions: {
    // Performance score must be 90+
    'categories:performance': ['error', { minScore: 0.9 }],

    // Accessibility score must be 90+
    'categories:accessibility': ['error', { minScore: 0.9 }],

    // Best practices score must be 90+
    'categories:best-practices': ['error', { minScore: 0.9 }],

    // SEO score must be 80+
    'categories:seo': ['warn', { minScore: 0.8 }],

    // Core Web Vitals
    'first-contentful-paint': ['error', { maxNumericValue: 2000 }],
    'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
    'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
    'total-blocking-time': ['error', { maxNumericValue: 300 }],
    'speed-index': ['error', { maxNumericValue: 3000 }],

    // Resource timing
    'server-response-time': ['error', { maxNumericValue: 600 }],
    interactive: ['error', { maxNumericValue: 3800 }],

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
    'no-console-logs': 'warn',
  },
};
