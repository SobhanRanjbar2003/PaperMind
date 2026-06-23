import { useTranslations } from 'next-intl';
import { Logo } from './logo';

export function Footer() {
  const t = useTranslations('Home');
  return (
    <footer className="border-t border-border/60 mt-24">
      <div className="container py-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
        <Logo />
        <p className="text-xs text-muted-foreground max-w-md">{t('ctaFooterBody')}</p>
      </div>
    </footer>
  );
}
