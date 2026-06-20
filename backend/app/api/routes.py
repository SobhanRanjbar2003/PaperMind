import os

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.schemas import (
    JobCreateResponse,
    JobResultResponse,
    JobStatus,
    JobStatusResponse,
    MindMapFlatNode,
    MindMapNode,
    MindMapResultResponse,
    MindMapStartResponse,
    MindMapStatus,
    MindMapStatusResponse,
    PresentationStartResponse,
    PresentationStatus,
    PresentationStatusResponse,
)
from app.services import job_manager, mindmap_manager, presentation_manager
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


# =========================================================
# --- اندپوینت‌های ساخت پاورپوینت از روی خلاصه ---
# =========================================================

@router.post("/jobs/{job_id}/presentation", response_model=PresentationStartResponse)
async def start_presentation(job_id: str, background_tasks: BackgroundTasks):
    """
    شروع ساخت پاورپوینت برای یک job که خلاصه‌سازی‌اش تمام شده.
    این کار شامل سه مرحله است: طراحی ساختار اسلاید با LLM، تولید تصاویر
    لازم با مدل تصویرساز (روی سرور آروان)، و ساخت نهایی فایل .pptx.
    """
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job پیدا نشد")

    if job["status"] != JobStatus.DONE:
        raise HTTPException(
            status_code=409,
            detail="ابتدا باید خلاصه‌سازی این job کامل شود (status باید 'done' باشد).",
        )

    existing = presentation_manager.get_presentation(job_id)
    if existing is not None and existing["status"] in (
        PresentationStatus.PENDING,
        PresentationStatus.PLANNING,
        PresentationStatus.GENERATING_IMAGES,
        PresentationStatus.BUILDING,
    ):
        raise HTTPException(
            status_code=409, detail="ساخت پاورپوینت برای این job در حال انجام است."
        )

    presentation_manager.start_presentation(job_id)
    background_tasks.add_task(presentation_manager.run_presentation_pipeline, job_id)

    return PresentationStartResponse(job_id=job_id, status=PresentationStatus.PENDING)


@router.get("/jobs/{job_id}/presentation", response_model=PresentationStatusResponse)
async def get_presentation_status(job_id: str):
    presentation = presentation_manager.get_presentation(job_id)
    if presentation is None:
        raise HTTPException(
            status_code=404,
            detail="هنوز ساخت پاورپوینتی برای این job شروع نشده است.",
        )

    download_url = (
        f"/api/jobs/{job_id}/presentation/download"
        if presentation["status"] == PresentationStatus.DONE
        else None
    )

    return PresentationStatusResponse(
        job_id=job_id,
        status=presentation["status"],
        progress=presentation["progress"],
        message=presentation["message"],
        slide_count=presentation["slide_count"],
        images_total=presentation["images_total"],
        images_done=presentation["images_done"],
        download_url=download_url,
    )


@router.get("/jobs/{job_id}/presentation/download")
async def download_presentation(job_id: str):
    presentation = presentation_manager.get_presentation(job_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="ارائه‌ای برای این job پیدا نشد.")

    if presentation["status"] == PresentationStatus.ERROR:
        raise HTTPException(
            status_code=500, detail=presentation["message"] or "ساخت پاورپوینت با خطا مواجه شد."
        )

    if presentation["status"] != PresentationStatus.DONE or not presentation["file_path"]:
        raise HTTPException(
            status_code=409, detail="فایل پاورپوینت هنوز آماده نیست."
        )

    job = job_manager.get_job(job_id)
    base_name = (job or {}).get("filename") or "presentation"
    base_name = os.path.splitext(base_name)[0]

    return FileResponse(
        path=presentation["file_path"],
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"{base_name}.pptx",
    )


# =========================================================
# --- اندپوینت‌های ساخت Mind Map (نقشه‌ی ذهنی) از روی خلاصه ---
# =========================================================

@router.post("/jobs/{job_id}/mindmap", response_model=MindMapStartResponse)
async def start_mindmap(job_id: str, background_tasks: BackgroundTasks):
    """
    شروع ساخت Mind Map برای job ای که خلاصه‌سازی‌اش تمام شده (شبیه Mind Map
    در NotebookLM). ساختار کلی از روی خلاصه و جزئیات عمیق‌تر از روی متن خام
    chunk های کتاب ساخته می‌شود.
    """
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job پیدا نشد")

    if job["status"] != JobStatus.DONE:
        raise HTTPException(
            status_code=409,
            detail="ابتدا باید خلاصه‌سازی این job کامل شود (status باید 'done' باشد).",
        )

    existing = mindmap_manager.get_mindmap(job_id)
    if existing is not None and existing["status"] in (
        MindMapStatus.PENDING,
        MindMapStatus.PLANNING,
        MindMapStatus.EXPANDING,
    ):
        raise HTTPException(
            status_code=409, detail="ساخت Mind Map برای این job در حال انجام است."
        )

    mindmap_manager.start_mindmap(job_id)
    background_tasks.add_task(mindmap_manager.run_mindmap_pipeline, job_id)

    return MindMapStartResponse(job_id=job_id, status=MindMapStatus.PENDING)


@router.get("/jobs/{job_id}/mindmap", response_model=MindMapStatusResponse)
async def get_mindmap_status(job_id: str):
    mindmap = mindmap_manager.get_mindmap(job_id)
    if mindmap is None:
        raise HTTPException(
            status_code=404,
            detail="هنوز ساخت Mind Map ای برای این job شروع نشده است.",
        )

    return MindMapStatusResponse(
        job_id=job_id,
        status=mindmap["status"],
        progress=mindmap["progress"],
        message=mindmap["message"],
        node_count=mindmap["node_count"],
        branch_count=mindmap["branch_count"],
        branches_done=mindmap["branches_done"],
    )


@router.get("/jobs/{job_id}/mindmap/result", response_model=MindMapResultResponse)
async def get_mindmap_result(job_id: str):
    mindmap = mindmap_manager.get_mindmap(job_id)
    if mindmap is None:
        raise HTTPException(status_code=404, detail="Mind Map ای برای این job پیدا نشد.")

    if mindmap["status"] == MindMapStatus.ERROR:
        raise HTTPException(status_code=500, detail=mindmap["message"] or "ساخت Mind Map با خطا مواجه شد.")

    if mindmap["status"] != MindMapStatus.DONE or not mindmap["result"]:
        raise HTTPException(status_code=409, detail="Mind Map هنوز آماده نیست.")

    result = mindmap["result"]
    return MindMapResultResponse(
        job_id=job_id,
        title=result["title"],
        max_depth=result["max_depth"],
        node_count=result["node_count"],
        tree=MindMapNode(**result["tree"]),
        nodes=[MindMapFlatNode(**n) for n in result["nodes"]],
        edges=result["edges"],
    )
