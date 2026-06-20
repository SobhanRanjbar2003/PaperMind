"""
مدیریت پایپلاین ساخت پاورپوینت از روی خلاصه‌ی یک job موجود.

این ماژول مستقل از job_manager است (حافظه‌ی in-memory جدا با کلید job_id)
تا بتوان بارها برای یک خلاصه، ارائه ساخت یا منطق summarization را دست‌نخورده
نگه داشت. مراحل:

  PENDING -> PLANNING -> GENERATING_IMAGES -> BUILDING -> DONE
                                                       (or -> ERROR at any stage)
"""

import asyncio
import logging
import os
import uuid

from app.config import settings
from app.schemas import PresentationStatus
from app.services import image_client, job_manager, pptx_builder, slide_planner

logger = logging.getLogger("presentation_manager")

# حافظه‌ی in-memory وضعیت ساخت ارائه، کلید = job_id (همان job خلاصه‌سازی)
PRESENTATIONS: dict[str, dict] = {}

_image_semaphore = asyncio.Semaphore(settings.image_max_concurrency)


def get_presentation(job_id: str) -> dict | None:
    return PRESENTATIONS.get(job_id)


def _output_dir() -> str:
    path = settings.presentation_output_dir
    os.makedirs(path, exist_ok=True)
    return path


def start_presentation(job_id: str) -> dict:
    """
    رکورد وضعیت ساخت ارائه را برای job_id می‌سازد (یا در صورت وجود، ریست می‌کند)
    تا توسط run_presentation_pipeline به صورت background پردازش شود.
    """
    presentation = {
        "status": PresentationStatus.PENDING,
        "progress": 0.0,
        "message": None,
        "file_path": None,
        "filename": None,
        "slide_count": 0,
        "images_total": 0,
        "images_done": 0,
    }
    PRESENTATIONS[job_id] = presentation
    return presentation


async def _generate_one_image(prompt: str, presentation: dict) -> bytes | None:
    try:
        async with _image_semaphore:
            image_bytes = await image_client.generate_image(prompt)
        presentation["images_done"] += 1
        return image_bytes
    except Exception as exc:  # noqa: BLE001
        presentation["images_done"] += 1
        logger.warning("تولید تصویر برای یک اسلاید ناموفق بود: %s", exc)
        if settings.image_fail_open:
            return None
        raise


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
        presentation["progress"] = 0.05

        plan = await slide_planner.build_slide_plan(
            job["summary"], source_filename=job.get("filename", "")
        )
        presentation["slide_count"] = len(plan["slides"]) + 2  # + عنوان + جمع‌بندی

        # --- مرحله ۲: تولید تصاویر لازم (موازی، با محدودیت همزمانی) ---
        presentation["status"] = PresentationStatus.GENERATING_IMAGES

        image_tasks: dict[int, str] = {
            idx: s["image_prompt"]
            for idx, s in enumerate(plan["slides"])
            if s.get("needs_image") and s.get("image_prompt")
        }
        cover_prompt = plan.get("cover_image_prompt") or ""

        presentation["images_total"] = len(image_tasks) + (1 if cover_prompt else 0)
        presentation["images_done"] = 0

        async def _run_indexed(idx: int, prompt: str):
            return idx, await _generate_one_image(prompt, presentation)

        coros = [_run_indexed(idx, prompt) for idx, prompt in image_tasks.items()]
        cover_coro = _generate_one_image(cover_prompt, presentation) if cover_prompt else None

        results = await asyncio.gather(*coros) if coros else []
        cover_image = await cover_coro if cover_coro is not None else None

        slide_images: dict[int, bytes] = {
            idx: img for idx, img in results if img is not None
        }
        presentation["progress"] = 0.7

        # --- مرحله ۳: ساخت فایل pptx نهایی ---
        presentation["status"] = PresentationStatus.BUILDING
        presentation["progress"] = 0.85

        filename = f"presentation_{job_id}.pptx"
        output_path = os.path.join(_output_dir(), filename)

        await asyncio.to_thread(
            pptx_builder.build_presentation, plan, slide_images, cover_image, output_path
        )

        presentation["file_path"] = output_path
        presentation["filename"] = filename
        presentation["status"] = PresentationStatus.DONE
        presentation["progress"] = 1.0

    except Exception as exc:  # noqa: BLE001
        logger.exception("ساخت پاورپوینت برای job %s ناموفق بود", job_id)
        presentation["status"] = PresentationStatus.ERROR
        presentation["message"] = str(exc)
