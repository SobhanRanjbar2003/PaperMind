import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';

type AnyStatus =
  | 'pending'
  | 'summarizing'
  | 'reducing'
  | 'planning'
  | 'expanding'
  | 'building'
  | 'generating'
  | 'done'
  | 'error';

const STATUS_VARIANT: Record<AnyStatus, 'default' | 'success' | 'destructive' | 'warning' | 'secondary'> = {
  pending: 'secondary',
  summarizing: 'default',
  reducing: 'default',
  planning: 'default',
  expanding: 'default',
  building: 'default',
  generating: 'default',
  done: 'success',
  error: 'destructive',
};

const STATUS_KEY: Record<AnyStatus, string> = {
  pending: 'statusPending',
  summarizing: 'statusSummarizing',
  reducing: 'statusReducing',
  planning: 'statusPlanning',
  expanding: 'statusExpanding',
  building: 'statusBuilding',
  generating: 'statusGenerating',
  done: 'statusDone',
  error: 'statusError',
};

export function StatusPill({ status, className }: { status: string; className?: string }) {
  const t = useTranslations('Job');
  const key = STATUS_KEY[status as AnyStatus] ?? 'statusPending';
  const variant = STATUS_VARIANT[status as AnyStatus] ?? 'secondary';
  return (
    <Badge variant={variant} className={cn('font-medium', className)}>
      <span
        className={cn(
          'me-1.5 inline-block h-1.5 w-1.5 rounded-full',
          status === 'done' && 'bg-emerald-500',
          status === 'error' && 'bg-destructive',
          status !== 'done' && status !== 'error' && 'bg-primary animate-pulse',
        )}
      />
      {t(key)}
    </Badge>
  );
}
