'use client';

import { useTranslations } from 'next-intl';
import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorState } from '@/components/ui/error-state';
import { Progress } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import { JobHeader } from '@/components/jobs/job-header';
import { JobTabs } from '@/components/jobs/job-tabs';
import { useJobsStore } from '@/store/jobs';
import { useJobStatus } from '@/hooks/use-jobs';
import {
  usePresentationStatus,
  useStartPresentation,
  useTemplates,
} from '@/hooks/use-presentation';
import { ApiClientError, presentationDownloadUrl } from '@/lib/api';
import { Download, Play, Presentation, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { PalettePicker } from './palette-picker';

export function PresentationView({ jobId }: { jobId: string }) {
  const t = useTranslations('Presentation');
  const tJob = useTranslations('Job');
  const tCommon = useTranslations('Common');

  const jobStatus = useJobStatus(jobId);
  const summaryReady = jobStatus.data?.status === 'done';

  const templates = useTemplates();
  const presentation = usePresentationStatus(jobId);
  const start = useStartPresentation();

  const recents = useJobsStore((s) => s.recents);
  const filename = useMemo(
    () => recents.find((r) => r.jobId === jobId)?.filename,
    [recents, jobId],
  );

  const [selected, setSelected] = useState<string | null>(null);

  const isNotStarted =
    presentation.isError &&
    presentation.error instanceof ApiClientError &&
    presentation.error.status === 404;
  const isBusy =
    presentation.data?.status === 'pending' ||
    presentation.data?.status === 'planning' ||
    presentation.data?.status === 'building' ||
    start.isPending;
  const isDone = presentation.data?.status === 'done';

  const handleGenerate = () => {
    start.mutate(
      { jobId, template: selected ?? undefined },
      {
        onSuccess: () => toast.success(t('buildingMessage')),
      },
    );
  };

  return (
    <>
      <JobHeader filename={filename} status={presentation.data?.status} />
      <JobTabs jobId={jobId} />

      <div className="container py-8">
        <div className="mb-6 flex items-end justify-between gap-3 flex-wrap">
          <div>
            <h2 className="font-display text-2xl font-semibold tracking-tight">{t('title')}</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t('subtitle')}</p>
          </div>
          {isDone ? (
            <div className="flex items-center gap-2">
              <Button asChild>
                <a href={presentationDownloadUrl(jobId)} download>
                  <Download className="h-4 w-4" /> {t('download')}
                </a>
              </Button>
              <Button variant="outline" size="sm" onClick={handleGenerate} disabled={start.isPending}>
                <RefreshCw className="h-3.5 w-3.5" />
                {t('regenerate')}
              </Button>
            </div>
          ) : null}
        </div>

        {!summaryReady ? (
          <EmptyState
            icon={<Presentation className="h-6 w-6" />}
            title={tJob('summaryEmpty')}
            description={tJob('summarySubtitle')}
          />
        ) : presentation.data?.status === 'error' ? (
          <ErrorState
            title={tCommon('error')}
            description={presentation.data.message ?? undefined}
            onRetry={handleGenerate}
            retryLabel={t('regenerate')}
          />
        ) : isBusy ? (
          <Card>
            <CardContent className="p-8">
              <div className="mb-3 flex items-center gap-2 text-sm">
                <Spinner />
                <span className="font-medium">
                  {presentation.data?.status === 'planning'
                    ? tJob('statusPlanning')
                    : presentation.data?.status === 'building'
                      ? tJob('statusBuilding')
                      : tJob('statusPending')}
                </span>
                <span className="ms-auto text-xs text-muted-foreground tabular-nums">
                  {Math.round((presentation.data?.progress ?? 0) * 100)}%
                </span>
              </div>
              <Progress value={Math.round((presentation.data?.progress ?? 0) * 100)} />
              {(presentation.data?.slide_count ?? 0) > 0 ? (
                <p className="mt-3 text-xs text-muted-foreground">
                  {t('slideCount', { count: presentation.data?.slide_count ?? 0 })}
                </p>
              ) : null}
            </CardContent>
          </Card>
        ) : isDone ? (
          <DoneCard jobId={jobId} slideCount={presentation.data?.slide_count ?? 0} template={presentation.data?.template ?? null} />
        ) : isNotStarted || presentation.data == null ? (
          <div className="grid gap-6 lg:grid-cols-[1.2fr,1fr]">
            <Card>
              <CardContent className="p-6">
                <h3 className="font-display text-lg font-semibold mb-1">{t('pickPalette')}</h3>
                <p className="text-sm text-muted-foreground mb-4">{t('subtitle')}</p>
                {templates.isPending ? (
                  <div className="space-y-2">
                    <div className="h-14 rounded-xl bg-muted animate-pulse" />
                    <div className="h-14 rounded-xl bg-muted animate-pulse" />
                    <div className="h-14 rounded-xl bg-muted animate-pulse" />
                  </div>
                ) : templates.data ? (
                  <PalettePicker
                    templates={templates.data.templates}
                    selected={selected}
                    onSelect={setSelected}
                    disabled={start.isPending}
                  />
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 flex flex-col h-full">
                <h3 className="font-display text-lg font-semibold">{t('emptyTitle')}</h3>
                <p className="text-sm text-muted-foreground mt-1">{t('emptyBody')}</p>
                {selected ? (
                  <p className="mt-3 text-sm">
                    <span className="text-muted-foreground">→ </span>
                    <span className="font-medium">{t('paletteSelected', { name: selected })}</span>
                  </p>
                ) : null}
                <div className="mt-auto pt-6">
                  <Button onClick={handleGenerate} size="lg" disabled={start.isPending} className="w-full">
                    <Play className="h-4 w-4" />
                    {t('generate')}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </div>
    </>
  );
}

function DoneCard({ jobId, slideCount, template }: { jobId: string; slideCount: number; template: string | null }) {
  const t = useTranslations('Presentation');
  return (
    <Card>
      <CardContent className="p-8 flex flex-col items-center text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <Presentation className="h-6 w-6" />
        </div>
        <h3 className="font-display text-xl font-semibold">{t('title')}</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          {t('slideCount', { count: slideCount })}
          {template ? ` · ${template}` : ''}
        </p>
        <Button asChild size="lg" className="mt-6">
          <a href={presentationDownloadUrl(jobId)} download>
            <Download className="h-4 w-4" /> {t('download')}
          </a>
        </Button>
      </CardContent>
    </Card>
  );
}
