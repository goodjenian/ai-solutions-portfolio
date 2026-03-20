import type { Metadata } from 'next';
import { Geist, Geist_Mono, Cinzel } from 'next/font/google';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { MainNav } from '@/components/layout/main-nav';
import { Providers } from '@/components/providers';
import { locales, type Locale } from '@/i18n/config';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

// Using Cinzel as a stand-in for "Phantom Templar" style
const fontTemplar = Cinzel({
  variable: '--font-templar',
  subsets: ['latin'],
});

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;

  const titles: Record<Locale, string> = {
    pl: 'Asystent Nieruchomości AI',
    en: 'AI Real Estate Assistant',
    ru: 'AI Ассистент по Недвижимости',
  };

  const descriptions: Record<Locale, string> = {
    pl: 'Nowoczesne wyszukiwanie nieruchomości i analityka rynkowa',
    en: 'Next-gen real estate search and analytics',
    ru: 'Современный поиск недвижимости и аналитика рынка',
  };

  return {
    title: {
      default: titles[locale as Locale] || titles.en,
      template: `%s | ${titles[locale as Locale] || titles.en}`,
    },
    description: descriptions[locale as Locale] || descriptions.en,
    viewport: {
      width: 'device-width',
      initialScale: 1,
      maximumScale: 1,
      userScalable: false,
    },
    alternates: {
      canonical: `/${locale}`,
      languages: {
        pl: '/pl',
        en: '/en',
        ru: '/ru',
      },
    },
    manifest: '/manifest.json',
    themeColor: '#2563eb',
    appleWebApp: {
      capable: true,
      statusBarStyle: 'default',
      title: 'AI Real Estate Assistant',
    },
    formatDetection: {
      telephone: false,
      date: true,
      address: true,
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  // Enable static rendering
  setRequestLocale(locale);

  // Providing all messages to the client
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function () {
                try {
                  var stored = localStorage.getItem("theme");
                  var theme = stored === "dark" || stored === "light" ? stored : null;
                  if (!theme) {
                    var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
                    theme = prefersDark ? "dark" : "light";
                  }
                  if (theme === "dark") document.documentElement.classList.add("dark");
                  else document.documentElement.classList.remove("dark");
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${fontTemplar.variable} antialiased min-h-screen flex flex-col`}
      >
        <NextIntlClientProvider messages={messages}>
          <Providers>
            <header className="border-b bg-background">
              <div className="relative flex h-16 items-center px-4 container mx-auto">
                <MainNav />
              </div>
            </header>
            <main className="flex-1">{children}</main>
          </Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
