'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  createJob,
  getJobResult,
  getJobStatus,
  startSummarize,
} from '@/lib/api';
import { env } from '@/lib/env';
import { isTerminalStatus } from '@/lib/utils';
import { useJobsStore } from '@/store/jobs';
import type { JobCreateResponse } from '@/types/api';

export const jobKeys = {
  all: ['jobs'] as const,
  status: (id: string) => ['jobs', id, 'status'] as const,
  result: (id: string) => ['jobs', id, 'result'] as const,
};

export function useCreateJob() {
  const addRecent = useJobsStore((s) => s.addRecent);

  return useMutation<JobCreateResponse, Error, File>({
    mutationFn: createJob,
    onSuccess: (data) => {
      addRecent({
        jobId: data.job_id,
        filename: data.filename,
        charCount: data.char_count,
        chunkCount: data.chunk_count,
        createdAt: Date.now(),
        lastStatus: 'pending',
      });
    },
    onError: (err) => {
      toast.error(err.message);
    },
  });
}

export function useStartSummarize() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => startSummarize(jobId),
    onSuccess: (_data, jobId) => {
      queryClient.invalidateQueries({ queryKey: jobKeys.status(jobId) });
    },
    onError: (err) => toast.error(err.message),
  });
}

export function useJobStatus(jobId: string | undefined, enabled = true) {
  const updateStatus = useJobsStore((s) => s.updateStatus);

  return useQuery({
    queryKey: jobKeys.status(jobId ?? ''),
    queryFn: () => getJobStatus(jobId as string),
    enabled: Boolean(jobId) && enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return env.pollIntervalMs;
      if (isTerminalStatus(data.status)) return false;
      return env.pollIntervalMs;
    },
    refetchIntervalInBackground: true,
    select: (data) => {
      if (jobId) updateStatus(jobId, data.status);
      return data;
    },
  });
}

export function useJobResult(jobId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: jobKeys.result(jobId ?? ''),
    queryFn: () => getJobResult(jobId as string),
    enabled: Boolean(jobId) && enabled,
  });
}
