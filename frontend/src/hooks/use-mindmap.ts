'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  getMindmapResult,
  getMindmapStatus,
  startMindmap,
  ApiClientError,
} from '@/lib/api';
import { env } from '@/lib/env';
import { isTerminalStatus } from '@/lib/utils';

export const mindmapKeys = {
  status: (id: string) => ['mindmap', id, 'status'] as const,
  result: (id: string) => ['mindmap', id, 'result'] as const,
};

export function useStartMindmap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => startMindmap(jobId),
    onSuccess: (_data, jobId) => {
      queryClient.invalidateQueries({ queryKey: mindmapKeys.status(jobId) });
    },
    onError: (err) => toast.error(err.message),
  });
}

export function useMindmapStatus(jobId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: mindmapKeys.status(jobId ?? ''),
    queryFn: () => getMindmapStatus(jobId as string),
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

export function useMindmapResult(jobId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: mindmapKeys.result(jobId ?? ''),
    queryFn: () => getMindmapResult(jobId as string),
    enabled: Boolean(jobId) && enabled,
  });
}
