'use client';

import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Play, RefreshCw } from 'lucide-react';
import { Spinner } from '@/components/ui/spinner';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';

interface QAControlsProps {
  count: number;
  setCount: (n: number) => void;
  onGenerate: () => void;
  generating: boolean;
  progress?: number;
  statusLabel?: string;
  canRegenerate?: boolean;
  defaultCount: number;
}

export function QAControls({
  count,
  setCount,
  onGenerate,
  generating,
  progress,
  statusLabel,
  canRegenerate,
  defaultCount,
}: QAControlsProps) {
  const t = useTranslations('QA');

  return (
    <Card className="mb-6">
      <CardContent className="p-4 sm:p-5">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="qa-count" className="text-xs text-muted-foreground">
              {t('countLabel')}
            </Label>
            <Input
              id="qa-count"
              type="number"
              min={1}
              max={20}
              value={count}
              onChange={(e) => {
                const next = Number(e.target.value);
                if (Number.isFinite(next)) {
                  setCount(Math.min(20, Math.max(1, Math.floor(next))));
                }
              }}
              className="w-24"
              disabled={generating}
            />
          </div>

          <Button onClick={onGenerate} disabled={generating}>
            {generating ? <Spinner /> : canRegenerate ? <RefreshCw className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {canRegenerate ? t('regenerate') : t('generate', { count })}
          </Button>

          <span className="text-xs text-muted-foreground">
            {`max 20 · default ${defaultCount}`}
          </span>
        </div>

        {generating || progress != null ? (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{statusLabel ?? '…'}</span>
              <span className="tabular-nums">{Math.round((progress ?? 0) * 100)}%</span>
            </div>
            <Progress value={Math.round((progress ?? 0) * 100)} />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
