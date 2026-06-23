'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  ApiClientError,
  getPresentationStatus,
  listTemplates,
  startPresentation,
} from '@/lib/api';
import { env } from '@/lib/env';
import { isTerminalStatus } from '@/lib/utils';

export const presentationKeys = {
  templates: ['presentation', 'templates'] as const,
  status: (id: string) => ['presentation', id, 'status'] as const,
};

export function useTemplates() {
  return useQuery({
    queryKey: presentationKeys.templates,
    queryFn: listTemplates,
    staleTime: 5 * 60 * 1000,
  });
}

export function useStartPresentation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, template }: { jobId: string; template?: string }) =>
      startPresentation(jobId, template),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: presentationKeys.status(vars.jobId) });
    },
    onError: (err) => toast.error(err.message),
  });
}

export function usePresentationStatus(jobId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: presentationKeys.status(jobId ?? ''),
    queryFn: () => getPresentationStatus(jobId as string),
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
