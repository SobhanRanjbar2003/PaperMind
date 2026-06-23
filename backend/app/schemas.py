from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ── Shared base ──────────────────────────────────────────────────────────────

class _JobStatusBase(BaseModel):
    job_id: str
    status: str
    progress: float
    message: Optional[str] = None


# ── Summarization ────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    PENDING = "pending"
    SUMMARIZING = "summarizing"
    REDUCING = "reducing"
    DONE = "done"
    ERROR = "error"


class JobCreateResponse(BaseModel):
    job_id: str
    filename: str
    char_count: int
    chunk_count: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    message: Optional[str] = None
    chunk_count: int = 0
    chunks_done: int = 0


class JobResultResponse(BaseModel):
    job_id: str
    summary: str
    word_count: int


# ── Presentation ─────────────────────────────────────────────────────────────

class PresentationStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    BUILDING = "building"
    DONE = "done"
    ERROR = "error"


class PresentationStartResponse(BaseModel):
    job_id: str
    status: PresentationStatus
    template: Optional[str] = None


class PresentationStatusResponse(BaseModel):
    job_id: str
    status: PresentationStatus
    progress: float
    message: Optional[str] = None
    slide_count: int = 0
    template: Optional[str] = None
    download_url: Optional[str] = None


# ── Mind Map ─────────────────────────────────────────────────────────────────

class MindMapStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXPANDING = "expanding"
    DONE = "done"
    ERROR = "error"


class MindMapNode(BaseModel):
    id: str
    label: str
    depth: int
    children: list["MindMapNode"] = []


MindMapNode.model_rebuild()


class MindMapEdge(BaseModel):
    id: str
    source: str
    target: str


class MindMapFlatNode(BaseModel):
    id: str
    label: str
    depth: int
    parent_id: Optional[str] = None


class MindMapStartResponse(BaseModel):
    job_id: str
    status: MindMapStatus


class MindMapStatusResponse(BaseModel):
    job_id: str
    status: MindMapStatus
    progress: float
    message: Optional[str] = None
    node_count: int = 0
    branch_count: int = 0
    branches_done: int = 0


class MindMapResultResponse(BaseModel):
    job_id: str
    title: str
    max_depth: int
    node_count: int
    tree: MindMapNode
    nodes: list[MindMapFlatNode]
    edges: list[MindMapEdge]


# ── Q&A shared ───────────────────────────────────────────────────────────────

class QAStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    DONE = "done"
    ERROR = "error"


class _QAStartResponse(BaseModel):
    job_id: str
    status: QAStatus
    count: int


class _QAStatusResponse(BaseModel):
    job_id: str
    status: QAStatus
    progress: float
    message: Optional[str] = None
    count: int = 0


# ── Multiple Choice ──────────────────────────────────────────────────────────

class MCOption(BaseModel):
    A: str
    B: str
    C: str
    D: str


class MCQuestion(BaseModel):
    id: int
    question: str
    options: MCOption
    answer: str
    explanation: str


class MCQStartResponse(_QAStartResponse):
    pass


class MCQStatusResponse(_QAStatusResponse):
    pass


class MCQResultResponse(BaseModel):
    job_id: str
    count: int
    questions: list[MCQuestion]


# ── Descriptive ──────────────────────────────────────────────────────────────

class DescriptiveQuestion(BaseModel):
    id: int
    question: str
    model_answer: str
    key_points: list[str]


class DescQStartResponse(_QAStartResponse):
    pass


class DescQStatusResponse(_QAStatusResponse):
    pass


class DescQResultResponse(BaseModel):
    job_id: str
    count: int
    questions: list[DescriptiveQuestion]


# ── Fill in the Blank ────────────────────────────────────────────────────────

class FillBlankQuestion(BaseModel):
    id: int
    sentence: str
    answer: str
    hint: str


class FillBlankStartResponse(_QAStartResponse):
    pass


class FillBlankStatusResponse(_QAStatusResponse):
    pass


class FillBlankResultResponse(BaseModel):
    job_id: str
    count: int
    questions: list[FillBlankQuestion]
