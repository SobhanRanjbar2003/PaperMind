"""
مدیریت پایپلاین ساخت Mind Map از روی خلاصه + متن خام یک job موجود.

مستقل از job_manager است (حافظه‌ی in-memory جدا با کلید job_id) تا منطق
خلاصه‌سازی دست‌نخورده بماند. مراحل:

  PENDING -> PLANNING -> EXPANDING -> DONE
                                   (or -> ERROR at any stage)

PLANNING: ۱ درخواست LLM روی خلاصه‌ی نهایی (ساختار کلی).
EXPANDING: حداکثر «تعداد شاخه‌ی اصلی» درخواست LLM موازی، با کمک متن خام
           chunk های کتاب، برای عمیق‌تر کردن هر شاخه.
"""

import logging

from app.config import settings
from app.schemas import MindMapStatus
from app.services import job_manager, mindmap_builder

logger = logging.getLogger("mindmap_manager")

# حافظه‌ی in-memory وضعیت ساخت mind map، کلید = job_id (همان job خلاصه‌سازی)
MINDMAPS: dict[str, dict] = {}


def get_mindmap(job_id: str) -> dict | None:
    return MINDMAPS.get(job_id)


def start_mindmap(job_id: str) -> dict:
    """
    رکورد وضعیت ساخت mind map را برای job_id می‌سازد (یا در صورت وجود، ریست
    می‌کند) تا توسط run_mindmap_pipeline به صورت background پردازش شود.
    """
    mindmap = {
        "status": MindMapStatus.PENDING,
        "progress": 0.0,
        "message": None,
        "node_count": 0,
        "branch_count": 0,
        "branches_done": 0,
        "result": None,  # دیکشنری نهایی: title/max_depth/node_count/tree/nodes/edges
    }
    MINDMAPS[job_id] = mindmap
    return mindmap


async def run_mindmap_pipeline(job_id: str) -> None:
    mindmap = MINDMAPS.get(job_id)
    job = job_manager.get_job(job_id)

    if mindmap is None:
        return

    if job is None or job["status"] != "done" or not job.get("summary"):
        mindmap["status"] = MindMapStatus.ERROR
        mindmap["message"] = "خلاصه‌ی این job آماده نیست؛ ابتدا باید خلاصه‌سازی کامل شود."
        return

    try:
        # --- مرحله ۱: ساخت ساختار کلی (ریشه + شاخه‌های اصلی) از روی خلاصه ---
        mindmap["status"] = MindMapStatus.PLANNING
        mindmap["progress"] = 0.05

        root = await mindmap_builder.build_first_pass(job["summary"])

        branches = root.get("children") or []
        mindmap["branch_count"] = len(branches)
        mindmap["branches_done"] = 0
        mindmap["progress"] = 0.25

        # --- مرحله ۲: تعمیق هر شاخه با متن خام chunk های مرتبط (موازی) ---
        mindmap["status"] = MindMapStatus.EXPANDING

        def _on_branch_done() -> None:
            mindmap["branches_done"] += 1
            done = mindmap["branches_done"]
            total = max(mindmap["branch_count"], 1)
            mindmap["progress"] = 0.25 + 0.65 * (done / total)

        chunks = job.get("chunks") or []
        root = await mindmap_builder.expand_branches(root, chunks, on_branch_done=_on_branch_done)

        # --- نهایی‌سازی: تخصیص id، محدودسازی عمق، خروجی tree + nodes/edges ---
        tree, nodes, edges = mindmap_builder.assign_ids_and_flatten(
            root, settings.mindmap_max_depth
        )

        mindmap["result"] = {
            "title": tree["label"],
            "max_depth": settings.mindmap_max_depth,
            "node_count": len(nodes),
            "tree": tree,
            "nodes": nodes,
            "edges": edges,
        }
        mindmap["node_count"] = len(nodes)
        mindmap["status"] = MindMapStatus.DONE
        mindmap["progress"] = 1.0

    except Exception as exc:  # noqa: BLE001
        logger.exception("ساخت mind map برای job %s ناموفق بود", job_id)
        mindmap["status"] = MindMapStatus.ERROR
        mindmap["message"] = str(exc)
