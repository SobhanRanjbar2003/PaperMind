'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useJobsStore } from '@/store/jobs';
import { Link } from '@/i18n/routing';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { BookOpen, Plus, Trash2, X } from 'lucide-react';
import { formatRelativeTime } from '@/lib/utils';
import { useEffect, useState } from 'react';

export function LibraryView() {
  const t = useTranslations('Library');
  const tCommon = useTranslations('Common');
  const locale = useLocale();
  const recents = useJobsStore((s) => s.recents);
  const remove = useJobsStore((s) => s.remove);
  const clear = useJobsStore((s) => s.clear);

  // Avoid hydration mismatch — store is persisted to localStorage
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div className="container py-10">
      <div className="mb-8 flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">{t('title')}</h1>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground">{t('subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          {mounted && recents.length > 0 ? (
            <Button variant="ghost" size="sm" onClick={clear}>
              <Trash2 className="h-3.5 w-3.5" />
              {t('clearAll')}
            </Button>
          ) : null}
          <Button asChild size="sm">
            <Link href="/">
              <Plus className="h-3.5 w-3.5" />
              {t('uploadAnother')}
            </Link>
          </Button>
        </div>
      </div>

      {!mounted ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Card key={i} className="h-32 animate-pulse" />
          ))}
        </div>
      ) : recents.length === 0 ? (
        <EmptyState
          icon={<BookOpen className="h-6 w-6" />}
          title={t('emptyTitle')}
          description={t('emptyBody')}
          action={
            <Button asChild>
              <Link href="/">{t('uploadAnother')}</Link>
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {recents.map((r) => (
            <Card key={r.jobId} className="group relative transition-all hover:shadow-md hover:border-primary/40">
              <button
                onClick={() => remove(r.jobId)}
                className="absolute end-3 top-3 rounded-md opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-accent"
                aria-label={t('removeJob')}
              >
                <X className="h-3.5 w-3.5" />
              </button>
              <Link href={`/jobs/${r.jobId}`} className="block">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <BookOpen className="h-3.5 w-3.5" />
                    <span>
                      {r.chunkCount}{' '}
                      {locale === 'fa' ? 'بخش' : r.chunkCount === 1 ? 'chunk' : 'chunks'}
                    </span>
                  </div>
                  <CardTitle className="line-clamp-2 mt-2 text-base">{r.filename}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    {t('createdRelative', {
                      time: formatRelativeTime(r.createdAt, locale),
                    })}
                  </p>
                  <div className="mt-3 flex items-center gap-1 text-xs font-medium text-primary">
                    {t('openJob')} <span className="rtl:rotate-180">→</span>
                  </div>
                </CardContent>
              </Link>
            </Card>
          ))}
        </div>
      )}
      <div className="sr-only">{tCommon('loading')}</div>
    </div>
  );
}
