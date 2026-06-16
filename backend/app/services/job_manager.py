import uuid

from app.config import settings
from app.schemas import JobStatus
from app.services import summarizer
from app.services.chunking import chunk_text

# توجه: این یک حافظه‌ی in-memory ساده برای dev است.
# برای production باید با redis/db جایگزین شود (هم برای persistence
# و هم برای پشتیبانی از چند instance/worker).
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

        # --- مرحله Map: خلاصه‌ی هر chunk ---
        job["status"] = JobStatus.SUMMARIZING
        chunk_summaries: list[str] = []
        total_steps = len(chunks) + 2  # + reduce + final به صورت تقریبی

        for i, chunk in enumerate(chunks):
            chunk_summary = await summarizer.summarize_chunk(chunk)
            chunk_summaries.append(chunk_summary)
            job["chunks_done"] = i + 1
            job["progress"] = (i + 1) / total_steps

        # --- مرحله Reduce: ادغام تدریجی خلاصه‌ها ---
        job["status"] = JobStatus.REDUCING
        current = chunk_summaries
        group_size = max(settings.max_group_size, 2)

        while len(current) > 1:
            next_round: list[str] = []
            for i in range(0, len(current), group_size):
                group = current[i : i + group_size]
                if len(group) == 1:
                    next_round.append(group[0])
                else:
                    merged = await summarizer.reduce_summaries(group)
                    next_round.append(merged)
            current = next_round
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
