'use client';

import { Link } from '@/i18n/routing';
import { useTranslations } from 'next-intl';
import { Logo } from './logo';
import { ThemeToggle } from './theme-toggle';
import { LanguageToggle } from './language-toggle';
import { Button } from '@/components/ui/button';
import { Search, Library, PanelLeft } from 'lucide-react';
import { useUIStore } from '@/store/ui';
import { Kbd } from '@/components/ui/kbd';

export function Navbar() {
  const t = useTranslations('Nav');
  const setCommandOpen = useUIStore((s) => s.setCommandOpen);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/60 glass">
      <div className="container flex h-14 items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="md:hidden"
          aria-label={t('menu')}
        >
          <PanelLeft className="h-[18px] w-[18px]" />
        </Button>

        <Link href="/" className="flex items-center gap-2">
          <Logo />
        </Link>

        <nav className="ml-6 hidden items-center gap-1 md:flex">
          <Link
            href="/"
            className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            {t('home')}
          </Link>
          <Link
            href="/library"
            className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            {t('library')}
          </Link>
        </nav>

        <div className="ms-auto flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCommandOpen(true)}
            className="hidden lg:inline-flex gap-2 text-muted-foreground"
            aria-label={t('openSearch')}
          >
            <Search className="h-3.5 w-3.5" />
            <span>{t('openSearch')}</span>
            <Kbd className="ms-2">⌘K</Kbd>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setCommandOpen(true)}
            aria-label={t('openSearch')}
          >
            <Search className="h-[18px] w-[18px]" />
          </Button>

          <Link href="/library" aria-label={t('library')} className="md:hidden">
            <Button variant="ghost" size="icon">
              <Library className="h-[18px] w-[18px]" />
            </Button>
          </Link>

          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
