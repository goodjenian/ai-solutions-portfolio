export const locales = ['pl', 'en', 'ru'] as const;
export const defaultLocale = 'pl' as const;

export type Locale = (typeof locales)[number];

export const localeNames: Record<Locale, string> = {
  pl: 'Polski',
  en: 'English',
  ru: 'Русский',
};

export const localeFlags: Record<Locale, string> = {
  pl: '🇵🇱',
  en: '🇬🇧',
  ru: '🇷🇺',
};

/**
 * Validates if a string is a valid locale
 */
export function isValidLocale(locale: string): locale is Locale {
  return locales.includes(locale as Locale);
}
