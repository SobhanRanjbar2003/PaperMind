import { NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Inter, Space_Grotesk } from 'next/font/google';
import type { ReactNode } from 'react';
import { localeDirection, routing } from '@/i18n/routing';
import { AppProviders } from '@/lib/providers';
import { Navbar } from '@/components/layout/navbar';
import { CommandPalette } from '@/components/layout/command-palette';
import { KeyboardShortcuts } from '@/components/layout/keyboard-shortcuts';
import { ErrorBoundary } from '@/components/layout/error-boundary';
import { TooltipProvider } from '@/components/ui/tooltip';

const sans = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const display = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
});

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!(routing.locales as readonly string[]).includes(locale)) {
    notFound();
  }
  setRequestLocale(locale);
  const messages = await getMessages();
  const dir = localeDirection[locale as (typeof routing.locales)[number]] ?? 'ltr';

  return (
    <html lang={locale} dir={dir} suppressHydrationWarning>
      <body className={`${sans.variable} ${display.variable} font-sans`}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <AppProviders>
            <TooltipProvider delayDuration={150}>
              <KeyboardShortcuts />
              <CommandPalette />
              <div className="relative flex min-h-screen flex-col">
                <Navbar />
                <ErrorBoundary>
                  <main className="flex-1">{children}</main>
                </ErrorBoundary>
              </div>
            </TooltipProvider>
          </AppProviders>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
