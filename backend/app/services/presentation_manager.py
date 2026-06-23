"""
مدیریت پایپلاین ساخت پاورپوینت از روی خلاصه‌ی یک job موجود.

این ماژول مستقل از job_manager است (حافظه‌ی in-memory جدا با کلید job_id)
تا بتوان بارها برای یک خلاصه، ارائه ساخت یا منطق summarization را دست‌نخورده
نگه داشت. مراحل:

  PENDING -> PLANNING -> BUILDING -> DONE
                                  (or -> ERROR at any stage)

توجه: تولید تصویر حذف شده است. اسلایدهایی که layout آن‌ها image-right/image-left
است با shape تزئینی جایگزین رندر می‌شوند (منطق fallback از پیش در pptx_builder
پیاده‌سازی شده).
"""

import asyncio
import logging
import os
import uuid

from app.config import settings
from app.schemas import PresentationStatus
from app.services import job_manager, pptx_builder, slide_planner

logger = logging.getLogger("presentation_manager")

# حافظه‌ی in-memory وضعیت ساخت ارائه، کلید = job_id (همان job خلاصه‌سازی)
PRESENTATIONS: dict[str, dict] = {}


def get_presentation(job_id: str) -> dict | None:
    return PRESENTATIONS.get(job_id)


def _output_dir() -> str:
    path = settings.presentation_output_dir
    os.makedirs(path, exist_ok=True)
    return path


def start_presentation(job_id: str, template: str | None = None) -> dict:
    """
    رکورد وضعیت ساخت ارائه را برای job_id می‌سازد (یا در صورت وجود، ریست می‌کند)
    تا توسط run_presentation_pipeline به صورت background پردازش شود.

    template: یکی از نام‌های قالب تعریف‌شده در slide_planner.PALETTES
              (مثلاً «Midnight Executive»). اگر None باشد، LLM قالب را انتخاب می‌کند.
    """
    presentation = {
        "status": PresentationStatus.PENDING,
        "progress": 0.0,
        "message": None,
        "file_path": None,
        "filename": None,
        "slide_count": 0,
        "template": template,
    }
    PRESENTATIONS[job_id] = presentation
    return presentation


async def run_presentation_pipeline(job_id: str) -> None:
    presentation = PRESENTATIONS.get(job_id)
    job = job_manager.get_job(job_id)

    if presentation is None:
        return

    if job is None or job["status"] != "done" or not job.get("summary"):
        presentation["status"] = PresentationStatus.ERROR
        presentation["message"] = "خلاصه‌ی این job آماده نیست؛ ابتدا باید خلاصه‌سازی کامل شود."
        return

    try:
        # --- مرحله ۱: طراحی ساختار اسلایدها با LLM ---
        presentation["status"] = PresentationStatus.PLANNING
        presentation["progress"] = 0.10

        forced_palette = presentation.get("template")

        plan = await slide_planner.build_slide_plan(
            job["summary"],
            source_filename=job.get("filename", ""),
            forced_palette=forced_palette,
        )
        presentation["slide_count"] = len(plan["slides"]) + 2  # + عنوان + جمع‌بندی
        presentation["progress"] = 0.60

        # --- مرحله ۲: ساخت فایل pptx نهایی (بدون تصویر) ---
        presentation["status"] = PresentationStatus.BUILDING
        presentation["progress"] = 0.75

        filename = f"presentation_{job_id}.pptx"
        output_path = os.path.join(_output_dir(), filename)

        # slide_images و cover_image هر دو خالی هستند (بدون تولید تصویر)
        await asyncio.to_thread(
            pptx_builder.build_presentation,
            plan,
            {},        # slide_images: خالی
            None,      # cover_image: بدون تصویر زمینه
            output_path,
        )

        presentation["file_path"] = output_path
        presentation["filename"] = filename
        presentation["status"] = PresentationStatus.DONE
        presentation["progress"] = 1.0

    except Exception as exc:  # noqa: BLE001
        logger.exception("ساخت پاورپوینت برای job %s ناموفق بود", job_id)
        presentation["status"] = PresentationStatus.ERROR
        presentation["message"] = str(exc)
