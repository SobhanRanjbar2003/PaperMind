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
