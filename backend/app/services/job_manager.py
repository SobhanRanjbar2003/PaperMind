import asyncio
import uuid

from app.config import settings
from app.schemas import JobStatus
from app.services import summarizer
from app.services.chunking import chunk_text

# توجه: این یک حافظه‌ی in-memory ساده برای یک instance/worker است.
# اگر در آینده نیاز به چند worker یا persistence افتاد، باید با redis/db
# جایگزین شود.
JOBS: dict[str, dict] = {}


def create_job(filename: str, text: str) -> tuple[str, dict]:
    job_id = str(uuid.uuid4())
    chunks = chunk_text(text, settings.chunk_size_chars, settings.chunk_overlap_chars)

    job = {
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
            job["status"] = JobStatus.ERROR
            job["message"] = "متنی برای خلاصه‌سازی پیدا نشد."
            return

        total_steps = len(chunks) + 2  # + reduce + final به صورت تقریبی

        # --- مرحله Map: خلاصه‌ی هر chunk (به صورت موازی) ---
        job["status"] = JobStatus.SUMMARIZING
        job["chunks_done"] = 0

        async def _summarize_with_progress(chunk: str) -> str:
            result = await summarizer.summarize_chunk(chunk)
            job["chunks_done"] += 1
            job["progress"] = job["chunks_done"] / total_steps
            return result

        chunk_summaries = await asyncio.gather(
            *[_summarize_with_progress(chunk) for chunk in chunks]
        )
        chunk_summaries = list(chunk_summaries)

        # --- مرحله Reduce: ادغام تدریجی خلاصه‌ها (هر دور به صورت موازی) ---
        job["status"] = JobStatus.REDUCING
        current = chunk_summaries
        group_size = max(settings.max_group_size, 2)

        while len(current) > 1:
            groups = [
                current[i : i + group_size] for i in range(0, len(current), group_size)
            ]

            async def _reduce_group(group: list[str]) -> str:
                if len(group) == 1:
                    return group[0]
                return await summarizer.reduce_summaries(group)

            current = list(await asyncio.gather(*[_reduce_group(g) for g in groups]))
            job["progress"] = min(job["progress"] + (1 / total_steps), 0.95)

        merged_text = current[0]

        # --- مرحله نهایی: تبدیل به خلاصه‌ی حدود N صفحه ---
        final_summary = await summarizer.finalize_summary(merged_text)

        job["summary"] = final_summary
        job["status"] = JobStatus.DONE
        job["progress"] = 1.0

    except Exception as exc:  # noqa: BLE001
        job["status"] = JobStatus.ERROR
        job["message"] = str(exc)
