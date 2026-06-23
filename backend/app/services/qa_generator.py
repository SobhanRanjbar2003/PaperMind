"""
Q&A generation from book summaries.
Supports three question types: multiple-choice, descriptive, fill-in-the-blank.
"""

import json
import re

from app.config import settings
from app.services import llm_client

# ── System prompts ────────────────────────────────────────────────────────────

_MCQ_SYSTEM = (
    "تو یک طراح سوال حرفه‌ای فارسی هستی. بر اساس متن خلاصه‌ی کتاب، "
    "سوالات چهارگزینه‌ای بساز. هر سوال باید:\n"
    "- دقیقاً ۴ گزینه داشته باشد (A، B، C، D)\n"
    "- یک گزینه‌ی درست مشخص داشته باشد\n"
    "- یک توضیح کوتاه برای پاسخ درست داشته باشد\n\n"
    "خروجی را فقط به صورت JSON خالص بده (بدون markdown backtick):\n"
    '{"questions": [{"id": 1, "question": "...", '
    '"options": {"A": "...", "B": "...", "C": "...", "D": "..."}, '
    '"answer": "A", "explanation": "..."}]}'
)

_DESCRIPTIVE_SYSTEM = (
    "تو یک طراح سوال حرفه‌ای فارسی هستی. بر اساس متن خلاصه‌ی کتاب، "
    "سوالات تشریحی (پاسخ باز) بساز. هر سوال باید:\n"
    "- نیاز به تفکر و تحلیل داشته باشد\n"
    "- یک پاسخ نمونه‌ی کامل و دقیق داشته باشد\n"
    "- نکات کلیدی پاسخ را مشخص کند\n\n"
    "خروجی را فقط به صورت JSON خالص بده (بدون markdown backtick):\n"
    '{"questions": [{"id": 1, "question": "...", '
    '"model_answer": "...", "key_points": ["نکته ۱", "نکته ۲"]}]}'
)

_FILL_BLANK_SYSTEM = (
    "تو یک طراح سوال حرفه‌ای فارسی هستی. بر اساس متن خلاصه‌ی کتاب، "
    "سوالات جای خالی بساز. هر سوال باید:\n"
    "- یک جمله‌ی کامل از متن (یا برگرفته از آن) باشد\n"
    "- یک یا دو کلمه‌ی کلیدی مهم حذف شده باشد (با ___ نشان داده شود)\n"
    "- پاسخ درست مشخص باشد\n"
    "- یک راهنمای کوتاه داشته باشد\n\n"
    "خروجی را فقط به صورت JSON خالص بده (بدون markdown backtick):\n"
    '{"questions": [{"id": 1, "sentence": "جمله با ___ ...", '
    '"answer": "کلمه", "hint": "راهنما"}]}'
)

_PROMPTS = {
    "multiple_choice": (_MCQ_SYSTEM, "سوالات چهارگزینه‌ای از مهم‌ترین مفاهیم"),
    "descriptive": (_DESCRIPTIVE_SYSTEM, "سوالات تشریحی عمیق از مهم‌ترین مفاهیم"),
    "fill_blank": (_FILL_BLANK_SYSTEM, "سوالات جای خالی از جملات کلیدی"),
}

_CODE_FENCE_RE = re.compile(r"```(?:json)?", re.IGNORECASE)


def _parse_json(raw: str) -> list[dict]:
    """Strip markdown fences and parse the questions list."""
    cleaned = _CODE_FENCE_RE.sub("", raw).strip().strip("`").strip()
    return json.loads(cleaned).get("questions", [])


async def _generate(qa_type: str, summary: str, count: int) -> list[dict]:
    system_prompt, description = _PROMPTS[qa_type]
    prompt = (
        f"خلاصه‌ی کتاب:\n\n{summary}\n\n"
        f"لطفاً دقیقاً {count} {description} این کتاب بساز."
    )
    raw = await llm_client.generate(
        prompt,
        system=system_prompt,
        model=settings.qa_llm_model or settings.llm_model,
        max_tokens=settings.qa_llm_max_tokens,
        temperature=settings.qa_llm_temperature,
    )
    return _parse_json(raw)


async def generate_multiple_choice(summary: str, count: int) -> list[dict]:
    return await _generate("multiple_choice", summary, count)


async def generate_descriptive(summary: str, count: int) -> list[dict]:
    return await _generate("descriptive", summary, count)


async def generate_fill_blank(summary: str, count: int) -> list[dict]:
    return await _generate("fill_blank", summary, count)
