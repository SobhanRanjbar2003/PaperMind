'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Eye, EyeOff, ListChecks } from 'lucide-react';
import { ApiClientError } from '@/lib/api';
import { useDescriptiveResult, useQAStatus, useStartQA } from '@/hooks/use-qa';
import { QAControls } from './qa-controls';
import { ErrorState } from '@/components/ui/error-state';
import { EmptyState } from '@/components/ui/empty-state';

const DEFAULT_COUNT = 5;

export function DescriptivePanel({ jobId }: { jobId: string }) {
  const t = useTranslations('QA');
  const tJob = useTranslations('Job');
  const [count, setCount] = useState(DEFAULT_COUNT);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});

  const status = useQAStatus(jobId, 'descriptive');
  const result = useDescriptiveResult(jobId, status.data?.status === 'done');
  const start = useStartQA();

  const isNotStarted =
    status.isError && status.error instanceof ApiClientError && status.error.status === 404;
  const generating =
    status.data?.status === 'generating' || status.data?.status === 'pending' || start.isPending;
  const isDone = status.data?.status === 'done';
  const isError = status.data?.status === 'error';

  return (
    <>
      <QAControls
        count={count}
        setCount={setCount}
        onGenerate={() => {
          setRevealed({});
          start.mutate({ jobId, type: 'descriptive', count });
        }}
        generating={generating}
        progress={status.data?.progress}
        statusLabel={tJob('statusGenerating')}
        canRegenerate={isDone}
        defaultCount={DEFAULT_COUNT}
      />

      {isError ? (
        <ErrorState title={tJob('summaryError')} description={status.data?.message ?? undefined} />
      ) : isNotStarted && !generating ? (
        <EmptyState
          icon={<ListChecks className="h-6 w-6" />}
          title={t('emptyTitle')}
          description={t('emptyBody')}
        />
      ) : isDone && result.data?.questions.length ? (
        <div className="space-y-4">
          {result.data.questions.map((q, idx) => {
            const isShown = !!revealed[q.id];
            return (
              <Card key={q.id}>
                <CardContent className="p-5">
                  <div className="flex items-start gap-3">
                    <Badge variant="secondary" className="mt-0.5">
                      {idx + 1}
                    </Badge>
                    <h4 className="text-base font-medium leading-snug flex-1">{q.question}</h4>
                  </div>

                  <div className="mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setRevealed((r) => ({ ...r, [q.id]: !r[q.id] }))}
                    >
                      {isShown ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      {isShown ? t('hideAnswer') : t('showAnswer')}
                    </Button>
                  </div>

                  {isShown ? (
                    <div className="mt-4 space-y-3">
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                          {t('modelAnswer')}
                        </p>
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {q.model_answer}
                        </p>
                      </div>
                      {q.key_points && q.key_points.length > 0 ? (
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                            {t('keyPoints')}
                          </p>
                          <ul className="list-disc ps-5 text-sm space-y-1">
                            {q.key_points.map((pt, i) => (
                              <li key={i}>{pt}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : null}
    </>
  );
}
