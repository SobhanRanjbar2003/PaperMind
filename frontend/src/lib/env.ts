// Centralized access to public environment variables.
// Never read process.env directly from components — go through here so
// missing values fail loudly and defaults stay consistent.

export const env = {
  apiUrl:
    (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) ||
    'http://localhost:8000',
  defaultLocale:
    (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_DEFAULT_LOCALE) || 'fa',
  pollIntervalMs: Number(
    (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_POLL_INTERVAL_MS) || 2000,
  ),
  appName:
    (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_APP_NAME) || 'PaperMind',
  appTagline:
    (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_APP_TAGLINE) ||
    'Turn books into summaries, mind maps, slides, and quizzes.',
} as const;
