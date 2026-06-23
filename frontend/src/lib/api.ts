import { env } from './env';
import type {
  DescQResultResponse,
  FillBlankResultResponse,
  JobCreateResponse,
  JobResultResponse,
  JobStatusResponse,
  MCQResultResponse,
  MindMapResultResponse,
  MindMapStartResponse,
  MindMapStatusResponse,
  PresentationStartResponse,
  PresentationStatusResponse,
  QAStartResponse,
  QAStatusResponse,
  QAType,
  TemplatesResponse,
} from '@/types/api';

class ApiClientError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail || `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = `${env.apiUrl}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init.body && !(init.body instanceof FormData)
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...init.headers,
      },
    });
  } catch (cause) {
    throw new ApiClientError(0, 'network_error');
  }

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body);
    } catch {
      try {
        detail = await response.text();
      } catch {
        // ignore
      }
    }
    throw new ApiClientError(response.status, detail);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

// ── Summarization ────────────────────────────────────────────────────────────

export async function createJob(file: File): Promise<JobCreateResponse> {
  const form = new FormData();
  form.append('file', file);
  return request<JobCreateResponse>('/api/jobs', {
    method: 'POST',
    body: form,
  });
}

export async function startSummarize(
  jobId: string,
): Promise<{ job_id: string; status: string }> {
  return request(`/api/jobs/${jobId}/summarize`, { method: 'POST' });
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return request<JobStatusResponse>(`/api/jobs/${jobId}`);
}

export async function getJobResult(jobId: string): Promise<JobResultResponse> {
  return request<JobResultResponse>(`/api/jobs/${jobId}/result`);
}

// ── Presentation ─────────────────────────────────────────────────────────────

export async function listTemplates(): Promise<TemplatesResponse> {
  return request<TemplatesResponse>('/api/presentations/templates');
}

export async function startPresentation(
  jobId: string,
  template?: string,
): Promise<PresentationStartResponse> {
  const query = template ? `?template=${encodeURIComponent(template)}` : '';
  return request<PresentationStartResponse>(
    `/api/jobs/${jobId}/presentation${query}`,
    { method: 'POST' },
  );
}

export async function getPresentationStatus(
  jobId: string,
): Promise<PresentationStatusResponse> {
  return request<PresentationStatusResponse>(`/api/jobs/${jobId}/presentation`);
}

export function presentationDownloadUrl(jobId: string): string {
  return `${env.apiUrl}/api/jobs/${jobId}/presentation/download`;
}

// ── Mind Map ─────────────────────────────────────────────────────────────────

export async function startMindmap(jobId: string): Promise<MindMapStartResponse> {
  return request<MindMapStartResponse>(`/api/jobs/${jobId}/mindmap`, {
    method: 'POST',
  });
}

export async function getMindmapStatus(jobId: string): Promise<MindMapStatusResponse> {
  return request<MindMapStatusResponse>(`/api/jobs/${jobId}/mindmap`);
}

export async function getMindmapResult(jobId: string): Promise<MindMapResultResponse> {
  return request<MindMapResultResponse>(`/api/jobs/${jobId}/mindmap/result`);
}

// ── Q&A ──────────────────────────────────────────────────────────────────────

export async function startQA(
  jobId: string,
  qaType: QAType,
  count?: number,
): Promise<QAStartResponse> {
  const query = count ? `?count=${count}` : '';
  return request<QAStartResponse>(`/api/jobs/${jobId}/qa/${qaType}${query}`, {
    method: 'POST',
  });
}

export async function getQAStatus(
  jobId: string,
  qaType: QAType,
): Promise<QAStatusResponse> {
  return request<QAStatusResponse>(`/api/jobs/${jobId}/qa/${qaType}`);
}

export async function getMCQResult(jobId: string): Promise<MCQResultResponse> {
  return request<MCQResultResponse>(`/api/jobs/${jobId}/qa/multiple-choice/result`);
}

export async function getDescriptiveResult(
  jobId: string,
): Promise<DescQResultResponse> {
  return request<DescQResultResponse>(`/api/jobs/${jobId}/qa/descriptive/result`);
}

export async function getFillBlankResult(
  jobId: string,
): Promise<FillBlankResultResponse> {
  return request<FillBlankResultResponse>(`/api/jobs/${jobId}/qa/fill-blank/result`);
}

export { ApiClientError };
