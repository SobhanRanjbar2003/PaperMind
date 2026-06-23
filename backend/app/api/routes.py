"""
API routes for the Book Summarizer service.

Structure:
  POST /api/jobs                              — upload & create job
  POST /api/jobs/{id}/summarize              — start summarization
  GET  /api/jobs/{id}                        — job status
  GET  /api/jobs/{id}/result                 — final summary

  GET  /api/presentations/templates          — list available templates
  POST /api/jobs/{id}/presentation           — start PPTX build
  GET  /api/jobs/{id}/presentation           — build status
  GET  /api/jobs/{id}/presentation/download  — download file

  POST /api/jobs/{id}/mindmap                — start mind map
  GET  /api/jobs/{id}/mindmap                — mind map status
  GET  /api/jobs/{id}/mindmap/result         — mind map data

  POST /api/jobs/{id}/qa/{type}              — start Q&A generation
  GET  /api/jobs/{id}/qa/{type}              — Q&A status
  GET  /api/jobs/{id}/qa/{type}/result       — Q&A results
"""

import os
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import (
    # Summarization
    JobCreateResponse, JobResultResponse, JobStatus, JobStatusResponse,
    # Mind Map
    MindMapEdge, MindMapFlatNode, MindMapNode, MindMapResultResponse,
    MindMapStartResponse, MindMapStatus, MindMapStatusResponse,
    # Presentation
    PresentationStartResponse, PresentationStatus, PresentationStatusResponse,
    # Q&A
    QAStatus,
    DescQResultResponse, DescQStartResponse, DescQStatusResponse, DescriptiveQuestion,
    FillBlankQuestion, FillBlankResultResponse, FillBlankStartResponse, FillBlankStatusResponse,
    MCOption, MCQResultResponse, MCQStartResponse, MCQStatusResponse, MCQuestion,
)
from app.services import job_manager, mindmap_manager, presentation_manager, qa_manager
from app.services.slide_planner import PALETTES
from app.services.text_extraction import extract_text

router = APIRouter(prefix="/api")

# ── Helpers ──────────────────────────────────────────────────────────────────

_QA_DEFAULT_COUNTS = {
    "multiple_choice": lambda: settings.qa_default_count_multiple_choice,
    "descriptive": lambda: settings.qa_default_count_descriptive,
    "fill_blank": lambda: settings.qa_default_count_fill_blank,
}

_ACTIVE_QA_STATUSES = (QAStatus.PENDING, QAStatus.GENERATING)


def _get_job_or_404(job_id: str) -> dict:
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job پیدا نشد")
    return job


def _require_done(job: dict) -> None:
    if job["status"] != JobStatus.DONE:
        raise HTTPException(
            status_code=409,
            detail="ابتدا باید خلاصه‌سازی این job کامل شود (status باید 'done' باشد).",
        )


def _resolve_qa_count(count: int | None, qa_type: str) -> int:
    resolved = count or _QA_DEFAULT_COUNTS[qa_type]()
    if resolved > settings.qa_max_count:
        raise HTTPException(
            status_code=400,
            detail=f"تعداد سوال نمی‌تواند بیشتر از {settings.qa_max_count} باشد.",
        )
    return resolved


# ── Summarization ─────────────────────────────────────────────────────────────

@router.post("/jobs", response_model=JobCreateResponse)
async def create_job(file: UploadFile = File(...)):
    """Upload a book file (PDF/DOCX/TXT/MD), extract text, and create a job."""
    content = await file.read()
    try:
        text = extract_text(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="متنی از این فایل استخراج نشد.")

    job_id, job = job_manager.create_job(file.filename, text)
    return JobCreateResponse(
        job_id=job_id,
        filename=file.filename,
        char_count=len(text),
        chunk_count=len(job["chunks"]),
    )


@router.post("/jobs/{job_id}/summarize")
async def start_summarize(job_id: str, background_tasks: BackgroundTasks):
    """Start the summarization pipeline as a background task."""
    job = _get_job_or_404(job_id)
    if job["status"] != JobStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"این job در وضعیت '{job['status']}' است و قابل شروع مجدد نیست.",
        )
    background_tasks.add_task(job_manager.run_pipeline, job_id)
    return {"job_id": job_id, "status": "started"}


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    job = _get_job_or_404(job_id)
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
    job = _get_job_or_404(job_id)
    if job["status"] == JobStatus.ERROR:
        raise HTTPException(status_code=500, detail=job["message"] or "خطای نامشخص")
    if job["status"] != JobStatus.DONE:
        raise HTTPException(status_code=409, detail="خلاصه هنوز آماده نیست.")
    summary = job["summary"] or ""
    return JobResultResponse(job_id=job_id, summary=summary, word_count=len(summary.split()))


# ── Presentation ──────────────────────────────────────────────────────────────

@router.get("/presentations/templates")
async def list_templates():
    """Return available color palette templates."""
    return {
        "templates": [
            {"name": name, "colors": colors, "description": _PALETTE_DESCRIPTIONS.get(name, "")}
            for name, colors in PALETTES.items()
        ]
    }


_PALETTE_DESCRIPTIONS = {
    "Midnight Executive": "آبی تیره کلاسیک — مناسب ارائه‌های رسمی و کسب‌وکاری",
    "Warm Terracotta": "قرمز خاکی گرم — مناسب موضوعات هنری، فرهنگی و انسانی",
    "Forest & Moss": "سبز جنگلی — مناسب موضوعات طبیعت، محیط زیست و علوم زیستی",
    "Coral Energy": "مرجانی پرانرژی — مناسب موضوعات خلاقانه و پرتحرک",
    "Ocean Depth": "آبی اقیانوسی — مناسب موضوعات علمی و تحقیقاتی",
    "Charcoal Minimal": "خاکستری مینیمال — مناسب موضوعات فنی و مهندسی",
    "Berry & Cream": "بری و کرم — مناسب موضوعات ادبی و روایی",
    "Sage Calm": "سبز آرام — مناسب موضوعات روان‌شناسی و رشد شخصی",
    "Cherry Bold": "قرمز گیلاسی — مناسب موضوعات تاریخی و حماسی",
    "Teal Trust": "فیروزه‌ای اعتماد — مناسب موضوعات اجتماعی و روابط",
}


@router.post("/jobs/{job_id}/presentation", response_model=PresentationStartResponse)
async def start_presentation(
    job_id: str,
    background_tasks: BackgroundTasks,
    template: Annotated[
        Optional[str],
        Query(description=f"نام قالب رنگی. یکی از: {', '.join(PALETTES.keys())}"),
    ] = None,
):
    """Start building a PPTX presentation from a completed summarization job."""
    job = _get_job_or_404(job_id)
    _require_done(job)

    if template is not None and template not in PALETTES:
        valid = ", ".join(f'"{n}"' for n in PALETTES)
        raise HTTPException(status_code=400, detail=f"قالب نامعتبر است. مقادیر مجاز: {valid}")

    existing = presentation_manager.get_presentation(job_id)
    if existing is not None and existing["status"] in (
        PresentationStatus.PENDING, PresentationStatus.PLANNING, PresentationStatus.BUILDING
    ):
        raise HTTPException(status_code=409, detail="ساخت پاورپوینت برای این job در حال انجام است.")

    presentation_manager.start_presentation(job_id, template=template)
    background_tasks.add_task(presentation_manager.run_presentation_pipeline, job_id)
    return PresentationStartResponse(job_id=job_id, status=PresentationStatus.PENDING, template=template)


@router.get("/jobs/{job_id}/presentation", response_model=PresentationStatusResponse)
async def get_presentation_status(job_id: str):
    presentation = presentation_manager.get_presentation(job_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="هنوز ساخت پاورپوینتی برای این job شروع نشده است.")

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
        template=presentation.get("template"),
        download_url=download_url,
    )


@router.get("/jobs/{job_id}/presentation/download")
async def download_presentation(job_id: str):
    presentation = presentation_manager.get_presentation(job_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="ارائه‌ای برای این job پیدا نشد.")
    if presentation["status"] == PresentationStatus.ERROR:
        raise HTTPException(status_code=500, detail=presentation["message"] or "ساخت پاورپوینت با خطا مواجه شد.")
    if presentation["status"] != PresentationStatus.DONE or not presentation["file_path"]:
        raise HTTPException(status_code=409, detail="فایل پاورپوینت هنوز آماده نیست.")

    job = job_manager.get_job(job_id)
    base = os.path.splitext((job or {}).get("filename") or "presentation")[0]
    return FileResponse(
        path=presentation["file_path"],
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"{base}.pptx",
    )


# ── Mind Map ──────────────────────────────────────────────────────────────────

@router.post("/jobs/{job_id}/mindmap", response_model=MindMapStartResponse)
async def start_mindmap(job_id: str, background_tasks: BackgroundTasks):
    """Start building a mind map from a completed summarization job."""
    job = _get_job_or_404(job_id)
    _require_done(job)

    existing = mindmap_manager.get_mindmap(job_id)
    if existing is not None and existing["status"] in (
        MindMapStatus.PENDING, MindMapStatus.PLANNING, MindMapStatus.EXPANDING
    ):
        raise HTTPException(status_code=409, detail="ساخت Mind Map برای این job در حال انجام است.")

    mindmap_manager.start_mindmap(job_id)
    background_tasks.add_task(mindmap_manager.run_mindmap_pipeline, job_id)
    return MindMapStartResponse(job_id=job_id, status=MindMapStatus.PENDING)


@router.get("/jobs/{job_id}/mindmap", response_model=MindMapStatusResponse)
async def get_mindmap_status(job_id: str):
    mindmap = mindmap_manager.get_mindmap(job_id)
    if mindmap is None:
        raise HTTPException(status_code=404, detail="هنوز ساخت Mind Map ای برای این job شروع نشده است.")
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
        edges=[MindMapEdge(**e) for e in result["edges"]],
    )


# ── Q&A ───────────────────────────────────────────────────────────────────────

def _start_qa_common(job_id: str, qa_type: str, count: int | None, background_tasks: BackgroundTasks) -> dict:
    job = _get_job_or_404(job_id)
    _require_done(job)
    resolved_count = _resolve_qa_count(count, qa_type)

    existing = qa_manager.get_qa(job_id, qa_type)
    if existing is not None and existing["status"] in _ACTIVE_QA_STATUSES:
        raise HTTPException(status_code=409, detail=f"تولید سوال '{qa_type}' برای این job در حال انجام است.")

    state = qa_manager.start_qa(job_id, qa_type, resolved_count)
    background_tasks.add_task(qa_manager.run_qa_pipeline, job_id, qa_type, job["summary"])
    return state


def _get_qa_state_or_404(job_id: str, qa_type: str) -> dict:
    state = qa_manager.get_qa(job_id, qa_type)
    if state is None:
        raise HTTPException(status_code=404, detail=f"هنوز تولید سوال '{qa_type}' برای این job شروع نشده است.")
    return state


# Multiple Choice

@router.post("/jobs/{job_id}/qa/multiple-choice", response_model=MCQStartResponse)
async def start_multiple_choice(
    job_id: str,
    background_tasks: BackgroundTasks,
    count: Annotated[Optional[int], Query(description="تعداد سوال (پیش‌فرض از config)")] = None,
):
    state = _start_qa_common(job_id, "multiple_choice", count, background_tasks)
    return MCQStartResponse(job_id=job_id, status=state["status"], count=state["count"])


@router.get("/jobs/{job_id}/qa/multiple-choice", response_model=MCQStatusResponse)
async def get_multiple_choice_status(job_id: str):
    state = _get_qa_state_or_404(job_id, "multiple_choice")
    return MCQStatusResponse(job_id=job_id, status=state["status"], progress=state["progress"],
                             message=state["message"], count=state["count"])


@router.get("/jobs/{job_id}/qa/multiple-choice/result", response_model=MCQResultResponse)
async def get_multiple_choice_result(job_id: str):
    state = _get_qa_state_or_404(job_id, "multiple_choice")
    if state["status"] == QAStatus.ERROR:
        raise HTTPException(status_code=500, detail=state["message"] or "خطا در تولید سوال تستی.")
    if state["status"] != QAStatus.DONE or not state["questions"]:
        raise HTTPException(status_code=409, detail="سوالات تستی هنوز آماده نیستند.")
    questions = [
        MCQuestion(id=q["id"], question=q["question"], options=MCOption(**q["options"]),
                   answer=q["answer"], explanation=q["explanation"])
        for q in state["questions"]
    ]
    return MCQResultResponse(job_id=job_id, count=len(questions), questions=questions)


# Descriptive

@router.post("/jobs/{job_id}/qa/descriptive", response_model=DescQStartResponse)
async def start_descriptive(
    job_id: str,
    background_tasks: BackgroundTasks,
    count: Annotated[Optional[int], Query(description="تعداد سوال (پیش‌فرض از config)")] = None,
):
    state = _start_qa_common(job_id, "descriptive", count, background_tasks)
    return DescQStartResponse(job_id=job_id, status=state["status"], count=state["count"])


@router.get("/jobs/{job_id}/qa/descriptive", response_model=DescQStatusResponse)
async def get_descriptive_status(job_id: str):
    state = _get_qa_state_or_404(job_id, "descriptive")
    return DescQStatusResponse(job_id=job_id, status=state["status"], progress=state["progress"],
                               message=state["message"], count=state["count"])


@router.get("/jobs/{job_id}/qa/descriptive/result", response_model=DescQResultResponse)
async def get_descriptive_result(job_id: str):
    state = _get_qa_state_or_404(job_id, "descriptive")
    if state["status"] == QAStatus.ERROR:
        raise HTTPException(status_code=500, detail=state["message"] or "خطا در تولید سوال تشریحی.")
    if state["status"] != QAStatus.DONE or not state["questions"]:
        raise HTTPException(status_code=409, detail="سوالات تشریحی هنوز آماده نیستند.")
    questions = [
        DescriptiveQuestion(id=q["id"], question=q["question"], model_answer=q["model_answer"],
                            key_points=q.get("key_points", []))
        for q in state["questions"]
    ]
    return DescQResultResponse(job_id=job_id, count=len(questions), questions=questions)


# Fill in the Blank

@router.post("/jobs/{job_id}/qa/fill-blank", response_model=FillBlankStartResponse)
async def start_fill_blank(
    job_id: str,
    background_tasks: BackgroundTasks,
    count: Annotated[Optional[int], Query(description="تعداد سوال (پیش‌فرض از config)")] = None,
):
    state = _start_qa_common(job_id, "fill_blank", count, background_tasks)
    return FillBlankStartResponse(job_id=job_id, status=state["status"], count=state["count"])


@router.get("/jobs/{job_id}/qa/fill-blank", response_model=FillBlankStatusResponse)
async def get_fill_blank_status(job_id: str):
    state = _get_qa_state_or_404(job_id, "fill_blank")
    return FillBlankStatusResponse(job_id=job_id, status=state["status"], progress=state["progress"],
                                   message=state["message"], count=state["count"])


@router.get("/jobs/{job_id}/qa/fill-blank/result", response_model=FillBlankResultResponse)
async def get_fill_blank_result(job_id: str):
    state = _get_qa_state_or_404(job_id, "fill_blank")
    if state["status"] == QAStatus.ERROR:
        raise HTTPException(status_code=500, detail=state["message"] or "خطا در تولید سوال جای خالی.")
    if state["status"] != QAStatus.DONE or not state["questions"]:
        raise HTTPException(status_code=409, detail="سوالات جای خالی هنوز آماده نیستند.")
    questions = [
        FillBlankQuestion(id=q["id"], sentence=q["sentence"], answer=q["answer"], hint=q.get("hint", ""))
        for q in state["questions"]
    ]
    return FillBlankResultResponse(job_id=job_id, count=len(questions), questions=questions)
