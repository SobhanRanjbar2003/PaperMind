'use client';

import { useTranslations } from 'next-intl';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import type { JobStatusResponse } from '@/types/api';

export function SummaryProgress({ status }: { status: JobStatusResponse }) {
  const t = useTranslations('Job');

  const label =
    status.status === 'summarizing'
      ? t('summarizing')
      : status.status === 'reducing'
        ? t('reducing')
        : status.status === 'pending'
          ? t('statusPending')
          : t('summaryDone');

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <CardTitle className="text-base">{label}</CardTitle>
          </div>
          <span className="text-xs text-muted-foreground tabular-nums">
            {Math.round((status.progress ?? 0) * 100)}%
          </span>
        </div>
        {status.chunk_count > 0 ? (
          <CardDescription>
            {t('progressChunks', {
              done: status.chunks_done,
              total: status.chunk_count,
            })}
          </CardDescription>
        ) : null}
      </CardHeader>
      <CardContent>
        <Progress value={Math.round((status.progress ?? 0) * 100)} />
        {status.message ? (
          <p className="mt-3 text-xs text-muted-foreground">{status.message}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
