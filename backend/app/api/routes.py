from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.schemas import (
    JobCreateResponse,
    JobResultResponse,
    JobStatus,
    JobStatusResponse,
)
from app.services import job_manager
from app.services.text_extraction import extract_text

router = APIRouter(prefix="/api")


@router.post("/jobs", response_model=JobCreateResponse)
async def create_job(file: UploadFile = File(...)):
    """
    فایل کتاب (pdf/docx/txt) را آپلود می‌کند، متن را استخراج و chunk می‌کند
    و یک job_id برمی‌گرداند که برای شروع خلاصه‌سازی استفاده می‌شود.
    """
    content = await file.read()

    try:
        text = extract_text(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not text.strip():
        raise HTTPException(
            status_code=400, detail="متنی از این فایل استخراج نشد."
        )

    job_id, job = job_manager.create_job(file.filename, text)

    return JobCreateResponse(
        job_id=job_id,
        filename=file.filename,
        char_count=len(text),
        chunk_count=len(job["chunks"]),
    )


@router.post("/jobs/{job_id}/summarize")
async def start_summarize(job_id: str, background_tasks: BackgroundTasks):
    """شروع پردازش خلاصه‌سازی به صورت background task."""
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job پیدا نشد")

    if job["status"] != JobStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"این job در وضعیت '{job['status']}' است و قابل شروع مجدد نیست.",
        )

    background_tasks.add_task(job_manager.run_pipeline, job_id)
    return {"job_id": job_id, "status": "started"}


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job پیدا نشد")

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        chunk_count=len(job["chunks"]),
        chunks_done=job["chunks_done"],
    )


@router.get("/jobs/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job پیدا نشد")

    if job["status"] == JobStatus.ERROR:
        raise HTTPException(status_code=500, detail=job["message"] or "خطای نامشخص")

    if job["status"] != JobStatus.DONE:
        raise HTTPException(
            status_code=409, detail="خلاصه هنوز آماده نیست، وضعیت job را چک کنید."
        )

    summary = job["summary"] or ""
    return JobResultResponse(
        job_id=job_id, summary=summary, word_count=len(summary.split())
    )
