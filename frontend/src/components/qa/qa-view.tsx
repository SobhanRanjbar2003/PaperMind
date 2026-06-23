'use client';

import { useTranslations } from 'next-intl';
import { useMemo } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ListChecks } from 'lucide-react';
import { JobHeader } from '@/components/jobs/job-header';
import { JobTabs } from '@/components/jobs/job-tabs';
import { EmptyState } from '@/components/ui/empty-state';
import { useJobsStore } from '@/store/jobs';
import { useJobStatus } from '@/hooks/use-jobs';
import { MCQPanel } from './mcq-panel';
import { DescriptivePanel } from './descriptive-panel';
import { FillBlankPanel } from './fill-blank-panel';

export function QAView({ jobId }: { jobId: string }) {
  const t = useTranslations('QA');
  const tJob = useTranslations('Job');
  const recents = useJobsStore((s) => s.recents);
  const filename = useMemo(
    () => recents.find((r) => r.jobId === jobId)?.filename,
    [recents, jobId],
  );

  const jobStatus = useJobStatus(jobId);
  const summaryReady = jobStatus.data?.status === 'done';

  return (
    <>
      <JobHeader filename={filename} status={jobStatus.data?.status} />
      <JobTabs jobId={jobId} />

      <div className="container py-8">
        <div className="mb-6">
          <h2 className="font-display text-2xl font-semibold tracking-tight">{t('title')}</h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t('subtitle')}</p>
        </div>

        {!summaryReady ? (
          <EmptyState
            icon={<ListChecks className="h-6 w-6" />}
            title={tJob('summaryEmpty')}
            description={tJob('summarySubtitle')}
          />
        ) : (
          <Tabs defaultValue="mcq">
            <TabsList>
              <TabsTrigger value="mcq">{t('tabMcq')}</TabsTrigger>
              <TabsTrigger value="descriptive">{t('tabDescriptive')}</TabsTrigger>
              <TabsTrigger value="fill-blank">{t('tabFillBlank')}</TabsTrigger>
            </TabsList>

            <TabsContent value="mcq">
              <MCQPanel jobId={jobId} />
            </TabsContent>

            <TabsContent value="descriptive">
              <DescriptivePanel jobId={jobId} />
            </TabsContent>

            <TabsContent value="fill-blank">
              <FillBlankPanel jobId={jobId} />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </>
  );
}
