"""
In-memory job store and summarization pipeline.

Note: single-process / single-worker only. Replace with Redis + Celery
or a task queue if horizontal scaling is needed.
"""

import asyncio
import uuid

from app.config import settings
from app.schemas import JobStatus
from app.services import summarizer
from app.services.chunking import chunk_text

JOBS: dict[str, dict] = {}


def create_job(filename: str, text: str) -> tuple[str, dict]:
    job_id = str(uuid.uuid4())
    chunks = chunk_text(text, settings.chunk_size_chars, settings.chunk_overlap_chars)
    job: dict = {
        "filename": filename,
        "chunks": chunks,
        "status": JobStatus.PENDING,
        "progress": 0.0,
        "message": None,
        "chunks_done": 0,
        "summary": None,
    }
    JOBS[job_id] = job
    return job_id, job


def get_job(job_id: str) -> dict | None:
    return JOBS.get(job_id)


async def run_pipeline(job_id: str) -> None:
    job = JOBS[job_id]
    try:
        chunks = job["chunks"]
        if not chunks:
            _set_error(job, "متنی برای خلاصه‌سازی پیدا نشد.")
            return

        total_steps = len(chunks) + 2  # rough: map steps + reduce + final

        # ── Map phase: summarize each chunk concurrently ──────────────────
        job["status"] = JobStatus.SUMMARIZING
        job["chunks_done"] = 0

        async def _map(chunk: str) -> str:
            result = await summarizer.summarize_chunk(chunk)
            job["chunks_done"] += 1
            job["progress"] = job["chunks_done"] / total_steps
            return result

        chunk_summaries: list[str] = list(
            await asyncio.gather(*(_map(c) for c in chunks))
        )

        # ── Reduce phase: hierarchically merge summaries ──────────────────
        job["status"] = JobStatus.REDUCING
        current = chunk_summaries
        group_size = max(settings.max_group_size, 2)

        while len(current) > 1:
            groups = [current[i: i + group_size] for i in range(0, len(current), group_size)]
            current = list(
                await asyncio.gather(*(_reduce_group(g) for g in groups))
            )
            job["progress"] = min(job["progress"] + 1 / total_steps, 0.95)

        # ── Final phase: rewrite into structured ~N-word summary ──────────
        job["summary"] = await summarizer.finalize_summary(current[0])
        job["status"] = JobStatus.DONE
        job["progress"] = 1.0

    except Exception as exc:  # noqa: BLE001
        _set_error(job, str(exc))


async def _reduce_group(group: list[str]) -> str:
    if len(group) == 1:
        return group[0]
    return await summarizer.reduce_summaries(group)


def _set_error(job: dict, message: str) -> None:
    job["status"] = JobStatus.ERROR
    job["message"] = message
