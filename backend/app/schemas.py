from enum import Enum
from typing import Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    PENDING = "pending"
    SUMMARIZING = "summarizing"  # مرحله map: خلاصه کردن chunk ها
    REDUCING = "reducing"  # مرحله reduce: ادغام خلاصه ها
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
    progress: float  # عددی بین 0 تا 1
    message: Optional[str] = None
    chunk_count: int = 0
    chunks_done: int = 0


class JobResultResponse(BaseModel):
    job_id: str
    summary: str
    word_count: int


class PresentationStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"  # طراحی ساختار اسلایدها با LLM
    GENERATING_IMAGES = "generating_images"  # تولید تصاویر با مدل تصویرساز
    BUILDING = "building"  # ساخت فایل pptx نهایی
    DONE = "done"
    ERROR = "error"


class PresentationStartResponse(BaseModel):
    job_id: str
    status: PresentationStatus


class PresentationStatusResponse(BaseModel):
    job_id: str
    status: PresentationStatus
    progress: float
    message: Optional[str] = None
    slide_count: int = 0
    images_total: int = 0
    images_done: int = 0
    download_url: Optional[str] = None


# =========================================================
# --- Mind Map ---
# =========================================================


class MindMapStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"  # ساخت ساختار کلی (ریشه + شاخه‌های اصلی) از روی خلاصه
    EXPANDING = "expanding"  # تعمیق هر شاخه با کمک متن خام chunk های مرتبط
    DONE = "done"
    ERROR = "error"


class MindMapNode(BaseModel):
    """یک نود درخت mind map. ساختار بازگشتی (هر نود می‌تواند children داشته باشد)."""

    id: str
    label: str
    depth: int
    children: list["MindMapNode"] = []


MindMapNode.model_rebuild()


class MindMapEdge(BaseModel):
    """یک یال، برای کتابخونه‌هایی مثل React Flow که نیاز به لیست مسطح nodes/edges دارند."""

    id: str
    source: str
    target: str


class MindMapFlatNode(BaseModel):
    """نمایش مسطح یک نود، سازگار با React Flow (بدون children تو در تو)."""

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
    # درخت تو در تو (مناسب برای markmap و رندرهای سلسله‌مراتبی مستقیم)
    tree: MindMapNode
    # نمایش مسطح nodes/edges (مناسب برای React Flow و کتابخونه‌های مشابه)
    nodes: list[MindMapFlatNode]
    edges: list[MindMapEdge]
