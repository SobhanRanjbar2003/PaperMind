"""
State management and pipeline execution for Q&A generation.
Three independent question types per job: multiple_choice, descriptive, fill_blank.
"""

import logging

from app.schemas import QAStatus
from app.services import qa_generator

logger = logging.getLogger(__name__)

# Keyed by (job_id, qa_type)
QA_JOBS: dict[tuple[str, str], dict] = {}

_GENERATORS = {
    "multiple_choice": qa_generator.generate_multiple_choice,
    "descriptive": qa_generator.generate_descriptive,
    "fill_blank": qa_generator.generate_fill_blank,
}


def start_qa(job_id: str, qa_type: str, count: int) -> dict:
    state: dict = {
        "qa_type": qa_type,
        "status": QAStatus.PENDING,
        "progress": 0.0,
        "message": None,
        "count": count,
        "questions": None,
    }
    QA_JOBS[(job_id, qa_type)] = state
    return state


def get_qa(job_id: str, qa_type: str) -> dict | None:
    return QA_JOBS.get((job_id, qa_type))


async def run_qa_pipeline(job_id: str, qa_type: str, summary: str) -> None:
    state = QA_JOBS.get((job_id, qa_type))
    if state is None:
        logger.error("QA state not found for job=%s type=%s", job_id, qa_type)
        return

    generator = _GENERATORS.get(qa_type)
    if generator is None:
        state["status"] = QAStatus.ERROR
        state["message"] = f"نوع سوال نامعتبر: {qa_type}"
        return

    try:
        state["status"] = QAStatus.GENERATING
        state["progress"] = 0.1
        state["message"] = "در حال تولید سوال..."

        questions = await generator(summary, state["count"])

        state["questions"] = questions
        state["count"] = len(questions)
        state["status"] = QAStatus.DONE
        state["progress"] = 1.0
        state["message"] = f"{len(questions)} سوال با موفقیت تولید شد."

    except Exception as exc:  # noqa: BLE001
        logger.exception("Q&A generation failed for job=%s type=%s", job_id, qa_type)
        state["status"] = QAStatus.ERROR
        state["message"] = str(exc)
