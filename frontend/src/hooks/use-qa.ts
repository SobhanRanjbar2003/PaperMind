'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  ApiClientError,
  getDescriptiveResult,
  getFillBlankResult,
  getMCQResult,
  getQAStatus,
  startQA,
} from '@/lib/api';
import { env } from '@/lib/env';
import { isTerminalStatus } from '@/lib/utils';
import type {
  DescQResultResponse,
  FillBlankResultResponse,
  MCQResultResponse,
  QAType,
} from '@/types/api';

export const qaKeys = {
  status: (id: string, type: QAType) => ['qa', id, type, 'status'] as const,
  result: (id: string, type: QAType) => ['qa', id, type, 'result'] as const,
};

export function useStartQA() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, type, count }: { jobId: string; type: QAType; count?: number }) =>
      startQA(jobId, type, count),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: qaKeys.status(vars.jobId, vars.type) });
    },
    onError: (err) => toast.error(err.message),
  });
}

export function useQAStatus(
  jobId: string | undefined,
  type: QAType,
  enabled = true,
) {
  return useQuery({
    queryKey: qaKeys.status(jobId ?? '', type),
    queryFn: () => getQAStatus(jobId as string, type),
    enabled: Boolean(jobId) && enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return env.pollIntervalMs;
      if (isTerminalStatus(data.status)) return false;
      return env.pollIntervalMs;
    },
    retry: (count, err) => {
      if (err instanceof ApiClientError && err.status === 404) return false;
      return count < 2;
    },
  });
}

export function useMCQResult(jobId: string | undefined, enabled = true) {
  return useQuery<MCQResultResponse>({
    queryKey: qaKeys.result(jobId ?? '', 'multiple-choice'),
    queryFn: () => getMCQResult(jobId as string),
    enabled: Boolean(jobId) && enabled,
  });
}

export function useDescriptiveResult(jobId: string | undefined, enabled = true) {
  return useQuery<DescQResultResponse>({
    queryKey: qaKeys.result(jobId ?? '', 'descriptive'),
    queryFn: () => getDescriptiveResult(jobId as string),
    enabled: Boolean(jobId) && enabled,
  });
}

export function useFillBlankResult(jobId: string | undefined, enabled = true) {
  return useQuery<FillBlankResultResponse>({
    queryKey: qaKeys.result(jobId ?? '', 'fill-blank'),
    queryFn: () => getFillBlankResult(jobId as string),
    enabled: Boolean(jobId) && enabled,
  });
}
