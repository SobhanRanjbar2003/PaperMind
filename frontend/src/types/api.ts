// Types mirroring the FastAPI backend's response models.
// Source: backend/app/schemas.py

export type JobStatus = 'pending' | 'summarizing' | 'reducing' | 'done' | 'error';
export type PresentationStatus = 'pending' | 'planning' | 'building' | 'done' | 'error';
export type MindMapStatus = 'pending' | 'planning' | 'expanding' | 'done' | 'error';
export type QAStatus = 'pending' | 'generating' | 'done' | 'error';

export type QAType = 'multiple-choice' | 'descriptive' | 'fill-blank';

export interface JobCreateResponse {
  job_id: string;
  filename: string;
  char_count: number;
  chunk_count: number;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  message: string | null;
  chunk_count: number;
  chunks_done: number;
}

export interface JobResultResponse {
  job_id: string;
  summary: string;
  word_count: number;
}

export interface PaletteColors {
  primary: string;
  secondary: string;
  accent: string;
  bg: string;
  style: string;
}

export interface PresentationTemplate {
  name: string;
  colors: PaletteColors;
  description: string;
}

export interface TemplatesResponse {
  templates: PresentationTemplate[];
}

export interface PresentationStartResponse {
  job_id: string;
  status: PresentationStatus;
  template: string | null;
}

export interface PresentationStatusResponse {
  job_id: string;
  status: PresentationStatus;
  progress: number;
  message: string | null;
  slide_count: number;
  template: string | null;
  download_url: string | null;
}

export interface MindMapNode {
  id: string;
  label: string;
  depth: number;
  children: MindMapNode[];
}

export interface MindMapFlatNode {
  id: string;
  label: string;
  depth: number;
  parent_id: string | null;
}

export interface MindMapEdge {
  id: string;
  source: string;
  target: string;
}

export interface MindMapStartResponse {
  job_id: string;
  status: MindMapStatus;
}

export interface MindMapStatusResponse {
  job_id: string;
  status: MindMapStatus;
  progress: number;
  message: string | null;
  node_count: number;
  branch_count: number;
  branches_done: number;
}

export interface MindMapResultResponse {
  job_id: string;
  title: string;
  max_depth: number;
  node_count: number;
  tree: MindMapNode;
  nodes: MindMapFlatNode[];
  edges: MindMapEdge[];
}

export interface MCOption {
  A: string;
  B: string;
  C: string;
  D: string;
}

export interface MCQuestion {
  id: number;
  question: string;
  options: MCOption;
  answer: 'A' | 'B' | 'C' | 'D';
  explanation: string;
}

export interface DescriptiveQuestion {
  id: number;
  question: string;
  model_answer: string;
  key_points: string[];
}

export interface FillBlankQuestion {
  id: number;
  sentence: string;
  answer: string;
  hint: string;
}

export interface QAStartResponse {
  job_id: string;
  status: QAStatus;
  count: number;
}

export interface QAStatusResponse {
  job_id: string;
  status: QAStatus;
  progress: number;
  message: string | null;
  count: number;
}

export interface MCQResultResponse {
  job_id: string;
  count: number;
  questions: MCQuestion[];
}

export interface DescQResultResponse {
  job_id: string;
  count: number;
  questions: DescriptiveQuestion[];
}

export interface FillBlankResultResponse {
  job_id: string;
  count: number;
  questions: FillBlankQuestion[];
}

export interface ApiError {
  detail: string;
  status?: number;
}
