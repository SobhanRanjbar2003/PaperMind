'use client';

import { useDropzone } from 'react-dropzone';
import { useTranslations } from 'next-intl';
import { useCallback, useState } from 'react';
import { CloudUpload, FileText, Loader2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useCreateJob, useStartSummarize } from '@/hooks/use-jobs';
import { useRouter } from '@/i18n/routing';
import { cn, formatBytes } from '@/lib/utils';

const ACCEPT = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
};

export function UploadDropzone() {
  const t = useTranslations('Upload');
  const create = useCreateJob();
  const start = useStartSummarize();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);

  const onDrop = useCallback(async (accepted: File[]) => {
    const f = accepted[0];
    if (!f) return;
    setFile(f);
    try {
      const job = await create.mutateAsync(f);
      await start.mutateAsync(job.job_id);
      toast.success(t('extracted', { chars: job.char_count, chunks: job.chunk_count }));
      router.push(`/jobs/${job.job_id}`);
    } catch {
      // toast already shown by mutation hook
      setFile(null);
    }
  }, [create, start, router, t]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPT,
    multiple: false,
    disabled: create.isPending || start.isPending,
  });

  const busy = create.isPending || start.isPending;

  return (
    <Card className="overflow-hidden">
      <div
        {...getRootProps()}
        className={cn(
          'relative flex flex-col items-center justify-center cursor-pointer transition-all duration-200 px-6 py-12',
          'border-2 border-dashed border-border rounded-xl',
          isDragActive && 'border-primary bg-primary/5',
          isDragReject && 'border-destructive bg-destructive/5',
          busy && 'pointer-events-none opacity-80',
        )}
      >
        <input {...getInputProps()} />

        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          {busy ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <CloudUpload className="h-7 w-7" />
          )}
        </div>

        <h3 className="font-display text-xl font-semibold tracking-tight">
          {isDragActive ? t('dropPromptHover') : t('dropPrompt')}
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">{t('browse')}</p>

        {file ? (
          <div className="mt-6 inline-flex items-center gap-2 rounded-full border bg-background px-3 py-1.5 text-xs">
            <FileText className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="font-medium truncate max-w-[200px]">{file.name}</span>
            <span className="text-muted-foreground">{formatBytes(file.size)}</span>
          </div>
        ) : null}

        <p className="mt-6 text-xs text-muted-foreground inline-flex items-center gap-1.5">
          <Sparkles className="h-3 w-3" />
          {t('limitsHint')}
        </p>

        <div className="absolute inset-0 -z-10 grid-bg opacity-30 dark:opacity-15 pointer-events-none" />
      </div>

      {busy ? (
        <div className="border-t border-border px-4 py-3 text-sm bg-muted/30 flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
          {t('uploading')}
        </div>
      ) : null}
    </Card>
  );
}
