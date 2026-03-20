import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Real Estate Assistant',
  description: 'Next-gen real estate search and analytics',
};

/**
 * Root layout - redirects to locale-specific layout.
 * The actual layout with navigation and providers is in [locale]/layout.tsx
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // This layout should not render anything - all content is in [locale]/layout.tsx
  // Next.js will automatically redirect to the default locale
  return children;
}
