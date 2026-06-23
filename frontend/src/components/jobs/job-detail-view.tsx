'use client';

import { useTranslations } from 'next-intl';
import { useEffect, useMemo } from 'react';
import { toast } from 'sonner';
import { Copy, Download, FileText, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ErrorState } from '@/components/ui/error-state';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { JobHeader } from '@/components/jobs/job-header';
import { JobTabs } from '@/components/jobs/job-tabs';
import { SummaryProgress } from '@/components/jobs/summary-progress';
import { useJobResult, useJobStatus, useStartSummarize } from '@/hooks/use-jobs';
import { useJobsStore } from '@/store/jobs';
import { ApiClientError } from '@/lib/api';

export function JobDetailView({ jobId }: { jobId: string }) {
  const t = useTranslations('Job');
  const tCommon = useTranslations('Common');

  const status = useJobStatus(jobId);
  const result = useJobResult(jobId, status.data?.status === 'done');
  const startSummarize = useStartSummarize();
  const recents = useJobsStore((s) => s.recents);
  const recentFilename = useMemo(
    () => recents.find((r) => r.jobId === jobId)?.filename,
    [recents, jobId],
  );

  // Auto-start summarization if backend reports pending and status hasn't transitioned
  useEffect(() => {
    if (status.data?.status === 'pending' && !startSummarize.isPending) {
      // Don't auto-start — user can press the button. This avoids race after manual restart.
    }
  }, [status.data?.status, startSummarize.isPending]);

  if (status.isError) {
    const isNotFound =
      status.error instanceof ApiClientError && status.error.status === 404;
    return (
      <>
        <JobHeader filename={recentFilename} />
        <div className="container py-10">
          <ErrorState
            title={isNotFound ? t('notFound') : tCommon('error')}
            description={
              isNotFound ? undefined : (status.error as Error).message ?? tCommon('errorBody')
            }
            onRetry={() => status.refetch()}
            retryLabel={tCommon('retry')}
          />
        </div>
      </>
    );
  }

  return (
    <>
      <JobHeader filename={recentFilename} status={status.data?.status} />
      <JobTabs jobId={jobId} />

      <div className="container py-8">
        {status.isPending ? (
          <SummarySkeleton />
        ) : status.data?.status === 'pending' ? (
          <EmptyState
            icon={<Play className="h-6 w-6" />}
            title={t('summaryEmpty')}
            description={t('summarySubtitle')}
            action={
              <Button onClick={() => startSummarize.mutate(jobId)} disabled={startSummarize.isPending}>
                <Play className="h-4 w-4" />
                {t('startSummarization')}
              </Button>
            }
          />
        ) : status.data?.status === 'summarizing' || status.data?.status === 'reducing' ? (
          <SummaryProgress status={status.data} />
        ) : status.data?.status === 'error' ? (
          <ErrorState
            title={t('summaryError')}
            description={status.data.message ?? undefined}
          />
        ) : status.data?.status === 'done' ? (
          <SummaryResultView jobId={jobId} loading={result.isPending} text={result.data?.summary} wordCount={result.data?.word_count} />
        ) : null}
      </div>
    </>
  );
}

function SummarySkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-6 w-1/3" />
      <Skeleton className="h-4 w-2/3" />
      <Card>
        <CardContent className="py-8 space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-[95%]" />
          <Skeleton className="h-4 w-[88%]" />
          <Skeleton className="h-4 w-[92%]" />
          <Skeleton className="h-4 w-[80%]" />
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryResultView({
  jobId,
  loading,
  text,
  wordCount,
}: {
  jobId: string;
  loading: boolean;
  text: string | undefined;
  wordCount: number | undefined;
}) {
  const t = useTranslations('Job');

  const onCopy = async () => {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    toast.success(t('copied'));
  };

  const onDownload = () => {
    if (!text) return;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `summary-${jobId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div>
          <h2 className="font-display text-2xl font-semibold tracking-tight">
            {t('summaryTitle')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('summarySubtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          {wordCount != null ? (
            <span className="text-xs text-muted-foreground">
              {t('wordCount', { count: wordCount })}
            </span>
          ) : null}
          <Button variant="outline" size="sm" onClick={onCopy} disabled={!text}>
            <Copy className="h-3.5 w-3.5" />
            {t('copy')}
          </Button>
          <Button variant="outline" size="sm" onClick={onDownload} disabled={!text}>
            <Download className="h-3.5 w-3.5" />
            {t('downloadTxt')}
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="py-8 px-6 sm:px-10">
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-[95%]" />
              <Skeleton className="h-4 w-[88%]" />
              <Skeleton className="h-4 w-[92%]" />
            </div>
          ) : text ? (
            <article className="prose prose-neutral dark:prose-invert max-w-none leading-relaxed whitespace-pre-wrap text-[15px]">
              {text}
            </article>
          ) : (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <FileText className="h-4 w-4" /> —
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
