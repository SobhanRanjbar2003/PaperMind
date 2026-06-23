import { defineRouting } from 'next-intl/routing';
import { createNavigation } from 'next-intl/navigation';

export const routing = defineRouting({
  locales: ['fa', 'en'],
  defaultLocale: 'fa',
  localePrefix: 'always',
});

export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);

export const localeDirection: Record<(typeof routing.locales)[number], 'rtl' | 'ltr'> = {
  fa: 'rtl',
  en: 'ltr',
};
