'use client';

import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorState } from '@/components/ui/error-state';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Network, Play, RefreshCw, Loader2 } from 'lucide-react';
import { JobHeader } from '@/components/jobs/job-header';
import { JobTabs } from '@/components/jobs/job-tabs';
import { useJobsStore } from '@/store/jobs';
import { useMemo, useState } from 'react';
import { useJobStatus } from '@/hooks/use-jobs';
import { useMindmapResult, useMindmapStatus, useStartMindmap } from '@/hooks/use-mindmap';
import { ApiClientError } from '@/lib/api';
import { MindmapCanvas } from './mindmap-canvas';

export function MindmapView({ jobId }: { jobId: string }) {
  const t = useTranslations('Mindmap');
  const tCommon = useTranslations('Common');
  const tJob = useTranslations('Job');

  const jobStatus = useJobStatus(jobId);
  const mindmapStatus = useMindmapStatus(jobId);
  const result = useMindmapResult(jobId, mindmapStatus.data?.status === 'done');
  const startMindmap = useStartMindmap();

  const recents = useJobsStore((s) => s.recents);
  const filename = useMemo(
    () => recents.find((r) => r.jobId === jobId)?.filename,
    [recents, jobId],
  );

  const [refreshKey, setRefreshKey] = useState(0);

  const isNotStarted =
    mindmapStatus.isError &&
    mindmapStatus.error instanceof ApiClientError &&
    mindmapStatus.error.status === 404;

  const isBusy =
    mindmapStatus.data?.status === 'pending' ||
    mindmapStatus.data?.status === 'planning' ||
    mindmapStatus.data?.status === 'expanding' ||
    startMindmap.isPending;

  const summaryReady = jobStatus.data?.status === 'done';

  return (
    <>
      <JobHeader filename={filename} status={mindmapStatus.data?.status} />
      <JobTabs jobId={jobId} />

      <div className="container py-8">
        <div className="mb-6 flex items-end justify-between gap-3 flex-wrap">
          <div>
            <h2 className="font-display text-2xl font-semibold tracking-tight">{t('title')}</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t('subtitle')}</p>
          </div>
          {mindmapStatus.data?.status === 'done' ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => startMindmap.mutate(jobId)}
              disabled={startMindmap.isPending}
            >
              <RefreshCw className="h-3.5 w-3.5" />
              {t('regenerate')}
            </Button>
          ) : null}
        </div>

        {!summaryReady ? (
          <EmptyState
            icon={<Network className="h-6 w-6" />}
            title={tJob('summaryEmpty')}
            description={tJob('summarySubtitle')}
          />
        ) : isNotStarted ? (
          <EmptyState
            icon={<Network className="h-6 w-6" />}
            title={t('emptyTitle')}
            description={t('emptyBody')}
            action={
              <Button onClick={() => startMindmap.mutate(jobId)} disabled={startMindmap.isPending}>
                <Play className="h-4 w-4" />
                {t('generate')}
              </Button>
            }
          />
        ) : mindmapStatus.data?.status === 'error' ? (
          <ErrorState
            title={tCommon('error')}
            description={mindmapStatus.data.message ?? undefined}
            onRetry={() => startMindmap.mutate(jobId)}
            retryLabel={t('regenerate')}
          />
        ) : isBusy ? (
          <Card>
            <CardContent className="p-8">
              <div className="mb-3 flex items-center gap-2 text-sm">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="font-medium">
                  {mindmapStatus.data?.status === 'planning'
                    ? tJob('statusPlanning')
                    : mindmapStatus.data?.status === 'expanding'
                      ? tJob('statusExpanding')
                      : tJob('statusPending')}
                </span>
                <span className="ms-auto text-xs text-muted-foreground tabular-nums">
                  {Math.round((mindmapStatus.data?.progress ?? 0) * 100)}%
                </span>
              </div>
              <Progress value={Math.round((mindmapStatus.data?.progress ?? 0) * 100)} />
              {(mindmapStatus.data?.branch_count ?? 0) > 0 ? (
                <p className="mt-3 text-xs text-muted-foreground">
                  {t('branchProgress', {
                    done: mindmapStatus.data?.branches_done ?? 0,
                    total: mindmapStatus.data?.branch_count ?? 0,
                  })}
                </p>
              ) : null}
            </CardContent>
          </Card>
        ) : result.data ? (
          <MindmapCanvas key={refreshKey} data={result.data} onReseed={() => setRefreshKey((k) => k + 1)} />
        ) : null}
      </div>
    </>
  );
}
