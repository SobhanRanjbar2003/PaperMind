import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';

export default function NotFound() {
  const t = useTranslations('Common');
  return (
    <div className="container py-24 flex flex-col items-center text-center">
      <span className="font-display text-6xl font-semibold tracking-tighter text-primary">404</span>
      <h1 className="mt-4 font-display text-2xl font-semibold">{t('error')}</h1>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">{t('errorBody')}</p>
      <Button asChild className="mt-6">
        <Link href="/">
          <Home className="h-4 w-4" />
          Home
        </Link>
      </Button>
    </div>
  );
}
