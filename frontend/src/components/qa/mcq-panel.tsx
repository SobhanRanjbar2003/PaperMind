'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Lightbulb, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ApiClientError } from '@/lib/api';
import { useMCQResult, useQAStatus, useStartQA } from '@/hooks/use-qa';
import type { MCQuestion } from '@/types/api';
import { QAControls } from './qa-controls';
import { ErrorState } from '@/components/ui/error-state';
import { EmptyState } from '@/components/ui/empty-state';
import { ListChecks } from 'lucide-react';

const DEFAULT_COUNT = 10;

export function MCQPanel({ jobId }: { jobId: string }) {
  const t = useTranslations('QA');
  const tJob = useTranslations('Job');
  const [count, setCount] = useState(DEFAULT_COUNT);

  const status = useQAStatus(jobId, 'multiple-choice');
  const result = useMCQResult(jobId, status.data?.status === 'done');
  const start = useStartQA();

  const isNotStarted =
    status.isError && status.error instanceof ApiClientError && status.error.status === 404;
  const generating =
    status.data?.status === 'generating' || status.data?.status === 'pending' || start.isPending;
  const isDone = status.data?.status === 'done';
  const isError = status.data?.status === 'error';

  const [answers, setAnswers] = useState<Record<number, 'A' | 'B' | 'C' | 'D' | undefined>>({});
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  const reset = () => {
    setAnswers({});
    setChecked({});
  };

  return (
    <>
      <QAControls
        count={count}
        setCount={setCount}
        onGenerate={() => {
          reset();
          start.mutate({ jobId, type: 'multiple-choice', count });
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
        <ScoreAndList
          questions={result.data.questions}
          answers={answers}
          setAnswers={setAnswers}
          checked={checked}
          setChecked={setChecked}
          onReset={reset}
        />
      ) : null}
    </>
  );
}

function ScoreAndList({
  questions,
  answers,
  setAnswers,
  checked,
  setChecked,
  onReset,
}: {
  questions: MCQuestion[];
  answers: Record<number, 'A' | 'B' | 'C' | 'D' | undefined>;
  setAnswers: (next: Record<number, 'A' | 'B' | 'C' | 'D' | undefined>) => void;
  checked: Record<number, boolean>;
  setChecked: (next: Record<number, boolean>) => void;
  onReset: () => void;
}) {
  const t = useTranslations('QA');
  const correctCount = questions.filter((q) => checked[q.id] && answers[q.id] === q.answer).length;
  const total = questions.length;
  const totalChecked = Object.values(checked).filter(Boolean).length;

  return (
    <div className="space-y-4">
      {totalChecked > 0 ? (
        <Card>
          <CardContent className="p-4 flex items-center justify-between flex-wrap gap-3">
            <div className="text-sm">
              <span className="font-semibold">{correctCount}</span>
              <span className="text-muted-foreground"> / {total} </span>
              <span className="text-muted-foreground">{t('scoreSummary', { correct: correctCount, total })}</span>
            </div>
            <Button variant="outline" size="sm" onClick={onReset}>
              <RotateCcw className="h-3.5 w-3.5" />
              {t('reset')}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {questions.map((q, idx) => {
        const userChoice = answers[q.id];
        const isChecked = checked[q.id];
        return (
          <Card key={q.id}>
            <CardContent className="p-5">
              <div className="flex items-start gap-3">
                <Badge variant="secondary" className="mt-0.5">
                  {idx + 1}
                </Badge>
                <h4 className="text-base font-medium leading-snug flex-1">{q.question}</h4>
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {(Object.keys(q.options) as Array<keyof typeof q.options>).map((key) => {
                  const value = q.options[key];
                  const isUser = userChoice === key;
                  const isCorrect = q.answer === key;
                  const showResult = isChecked;
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => {
                        if (isChecked) return;
                        setAnswers({ ...answers, [q.id]: key });
                      }}
                      className={cn(
                        'group flex items-start gap-3 rounded-lg border bg-card p-3 text-start transition-colors',
                        !showResult && isUser && 'border-primary ring-1 ring-primary/40 bg-primary/5',
                        showResult && isCorrect && 'border-emerald-500/60 bg-emerald-500/5',
                        showResult && isUser && !isCorrect && 'border-destructive/60 bg-destructive/5',
                        !showResult && 'hover:border-primary/40',
                      )}
                      disabled={isChecked}
                    >
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md border bg-background text-xs font-semibold">
                        {key}
                      </span>
                      <span className="text-sm flex-1">{value}</span>
                      {showResult && isCorrect ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      ) : showResult && isUser ? (
                        <XCircle className="h-4 w-4 text-destructive" />
                      ) : null}
                    </button>
                  );
                })}
              </div>

              {!isChecked ? (
                <div className="mt-4 flex justify-end">
                  <Button
                    size="sm"
                    onClick={() => setChecked({ ...checked, [q.id]: true })}
                    disabled={!userChoice}
                  >
                    {t('checkAnswer')}
                  </Button>
                </div>
              ) : (
                <div className="mt-4 rounded-lg border border-border bg-muted/30 p-3 text-sm flex items-start gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-500 mt-0.5" />
                  <div>
                    <p className="font-medium">{t('explanation')}</p>
                    <p className="mt-1 text-muted-foreground">{q.explanation}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
