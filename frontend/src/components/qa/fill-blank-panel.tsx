'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Lightbulb, ListChecks } from 'lucide-react';
import { ApiClientError } from '@/lib/api';
import { useFillBlankResult, useQAStatus, useStartQA } from '@/hooks/use-qa';
import { QAControls } from './qa-controls';
import { ErrorState } from '@/components/ui/error-state';
import { EmptyState } from '@/components/ui/empty-state';
import { cn } from '@/lib/utils';

const DEFAULT_COUNT = 10;

function normalize(s: string): string {
  return s.trim().toLocaleLowerCase().replace(/\s+/g, ' ');
}

export function FillBlankPanel({ jobId }: { jobId: string }) {
  const t = useTranslations('QA');
  const tJob = useTranslations('Job');

  const [count, setCount] = useState(DEFAULT_COUNT);
  const [inputs, setInputs] = useState<Record<number, string>>({});
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  const status = useQAStatus(jobId, 'fill-blank');
  const result = useFillBlankResult(jobId, status.data?.status === 'done');
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
          setInputs({});
          setChecked({});
          start.mutate({ jobId, type: 'fill-blank', count });
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
            const userValue = inputs[q.id] ?? '';
            const isChecked = checked[q.id];
            const correct = isChecked && normalize(userValue) === normalize(q.answer);
            return (
              <Card key={q.id}>
                <CardContent className="p-5">
                  <div className="flex items-start gap-3">
                    <Badge variant="secondary" className="mt-0.5">
                      {idx + 1}
                    </Badge>
                    <p className="text-base leading-snug flex-1 whitespace-pre-wrap">
                      {q.sentence}
                    </p>
                  </div>

                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <Input
                      value={userValue}
                      onChange={(e) => setInputs((m) => ({ ...m, [q.id]: e.target.value }))}
                      placeholder="…"
                      disabled={isChecked}
                      className={cn(
                        'max-w-xs',
                        isChecked && correct && 'border-emerald-500',
                        isChecked && !correct && 'border-destructive',
                      )}
                    />
                    {!isChecked ? (
                      <Button
                        size="sm"
                        onClick={() => setChecked((m) => ({ ...m, [q.id]: true }))}
                        disabled={!userValue.trim()}
                      >
                        {t('checkAnswer')}
                      </Button>
                    ) : correct ? (
                      <Badge variant="success" className="gap-1">
                        <CheckCircle2 className="h-3 w-3" /> {t('correct')}
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="gap-1">
                        <XCircle className="h-3 w-3" /> {t('incorrect')}
                      </Badge>
                    )}
                  </div>

                  {q.hint ? (
                    <div className="mt-3 inline-flex items-center gap-2 text-xs text-muted-foreground">
                      <Lightbulb className="h-3 w-3" />
                      <span className="font-medium">{t('hint')}:</span>
                      {q.hint}
                    </div>
                  ) : null}

                  {isChecked ? (
                    <p className="mt-3 text-sm">
                      <span className="text-muted-foreground">{t('modelAnswer')}: </span>
                      <span className="font-medium">{q.answer}</span>
                    </p>
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
