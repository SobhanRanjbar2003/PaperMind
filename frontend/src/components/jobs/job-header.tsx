'use client';

import { Link } from '@/i18n/routing';
import { useTranslations } from 'next-intl';
import { ArrowLeft, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { StatusPill } from '@/components/layout/status-pill';
import { Skeleton } from '@/components/ui/skeleton';
import { truncate } from '@/lib/utils';

interface JobHeaderProps {
  filename?: string;
  status?: string;
  rightSlot?: React.ReactNode;
}

export function JobHeader({ filename, status, rightSlot }: JobHeaderProps) {
  const t = useTranslations('Common');
  const tJob = useTranslations('Job');

  return (
    <div className="border-b border-border bg-background/80 backdrop-blur sticky top-14 z-30">
      <div className="container py-4 flex items-center gap-3 flex-wrap">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/library">
            <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
            {t('back')}
          </Link>
        </Button>

        <div className="h-6 w-px bg-border" />

        <div className="flex items-center gap-2 min-w-0">
          <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
          {filename ? (
            <>
              <span className="text-xs text-muted-foreground">{tJob('filename')}:</span>
              <span className="font-medium text-sm truncate" title={filename}>
                {truncate(filename, 60)}
              </span>
            </>
          ) : (
            <Skeleton className="h-4 w-48" />
          )}
        </div>

        <div className="ms-auto flex items-center gap-2">
          {status ? <StatusPill status={status} /> : <Skeleton className="h-5 w-16 rounded-full" />}
          {rightSlot}
        </div>
      </div>
    </div>
  );
}
