"""
Converts the final summary into a structured slide plan (JSON) via LLM,
then passes it to pptx_builder.

Each palette entry has:
  primary   — dominant background color (~60–70% visual weight)
  secondary — supporting / accent element color
  accent    — highlight / number badge color
  bg        — content slide background (usually white or very light)
  style     — visual style hint consumed by pptx_builder for motif choice
"""

import json
import logging
import re

from app.config import settings
from app.services import llm_client

logger = logging.getLogger(__name__)

# ── Palettes ──────────────────────────────────────────────────────────────────
# 10 professionally designed palettes — each with a distinct personality.
# "bg" is the content-slide background; "style" drives motif selection in builder.

PALETTES: dict[str, dict[str, str]] = {
    "Midnight Executive": {
        "primary": "1E2761",
        "secondary": "CADCFC",
        "accent": "F5A623",
        "bg": "FFFFFF",
        "style": "circles",
    },
    "Warm Terracotta": {
        "primary": "B85042",
        "secondary": "E7E8D1",
        "accent": "A7BEAE",
        "bg": "FAF7F2",
        "style": "rounded",
    },
    "Forest & Moss": {
        "primary": "2C5F2D",
        "secondary": "97BC62",
        "accent": "F5F5F5",
        "bg": "F4F9F4",
        "style": "leaf",
    },
    "Coral Energy": {
        "primary": "F96167",
        "secondary": "2F3C7E",
        "accent": "F9E795",
        "bg": "FFFFFF",
        "style": "bold",
    },
    "Ocean Depth": {
        "primary": "065A82",
        "secondary": "9DD9F3",
        "accent": "F5A623",
        "bg": "F0F8FF",
        "style": "wave",
    },
    "Charcoal Minimal": {
        "primary": "36454F",
        "secondary": "B0BEC5",
        "accent": "CFD8DC",
        "bg": "FAFAFA",
        "style": "minimal",
    },
    "Berry & Cream": {
        "primary": "6D2E46",
        "secondary": "A26769",
        "accent": "ECE2D0",
        "bg": "FDF8F3",
        "style": "rounded",
    },
    "Sage Calm": {
        "primary": "4A7C59",
        "secondary": "A8C5A0",
        "accent": "F0EAD6",
        "bg": "F7FBF7",
        "style": "leaf",
    },
    "Cherry Bold": {
        "primary": "990011",
        "secondary": "FCF6F5",
        "accent": "2F3C7E",
        "bg": "FFFFFF",
        "style": "bold",
    },
    "Teal Trust": {
        "primary": "028090",
        "secondary": "05C3DE",
        "accent": "F5F5F5",
        "bg": "F0FAFB",
        "style": "wave",
    },
}

DEFAULT_PALETTE = "Midnight Executive"

_VALID_LAYOUTS = {"image-right", "image-left", "bullets-only", "quote", "two-column", "stat"}

_PALETTE_LIST = ", ".join(f'"{name}"' for name in PALETTES)

SYSTEM_PROMPT = f"""تو یک طراح حرفه‌ای ارائه‌های کلاسی (PowerPoint) هستی که از روی خلاصه‌ی یک کتاب،
ساختار یک ارائه‌ی آموزشی کامل و قابل‌ارائه طراحی می‌کنی.

فقط و فقط یک JSON معتبر (بدون Markdown، بدون توضیح اضافه، بدون ```) با این ساختار دقیق برگردان:

{{
  "presentation_title": "عنوان کوتاه و جذاب ارائه (بر اساس موضوع کتاب)",
  "subtitle": "یک زیرعنوان کوتاه (مثلاً نام کتاب یا یک جمله توصیفی)",
  "palette": "یکی از این نام‌ها دقیقاً: {_PALETTE_LIST}",
  "slides": [
    {{
      "title": "تیتر کوتاه اسلاید (حداکثر ۶-۷ کلمه)",
      "layout": "یکی از: image-right, image-left, bullets-only, quote, two-column, stat",
      "bullets": ["نکته‌ی کوتاه ۱", "نکته‌ی کوتاه ۲", "نکته‌ی کوتاه ۳"],
      "speaker_notes": "یک یا دو جمله توضیح بیشتر برای ارائه‌دهنده (اختیاری)"
    }}
  ]
}}

قوانین مهم:
- تعداد اسلایدهای محتوایی (فهرست slides) باید بین __MIN_SLIDES__ تا __MAX_SLIDES__ باشد.
- محتوای هر اسلاید باید مستقیماً برگرفته از متن خلاصه باشد؛ چیزی از خودت اضافه نکن.
- هر اسلاید را حول یک ایده/فصل/بخش مشخص از خلاصه بساز تا اسلایدها پوشش کامل از کل خلاصه داشته باشند.
- هر بولت باید کوتاه باشد (حداکثر ۱۴-۱۶ کلمه). هر اسلاید بین ۳ تا ۵ بولت داشته باشد.
- layout را متنوع انتخاب کن (ترکیبی از همه‌ی layoutها) تا ارائه یکنواخت نشود.
- از layout «stat» برای اسلایدهایی با آمار، عدد یا مقایسه استفاده کن.
- از layout «two-column» برای مقایسه دو مفهوم یا دو بخش موازی استفاده کن (bullets دو بخش را با " | " جدا کن).
- از layout «quote» برای نقل‌قول‌ها یا جملات کلیدی مهم استفاده کن.
- اولین اسلاید باید مقدمه/کلیات کتاب و آخرین اسلاید باید جمع‌بندی/نتیجه‌گیری باشد.
- قالب رنگی (palette) را بر اساس موضوع کتاب هوشمندانه انتخاب کن (مثلاً Forest & Moss برای موضوعات طبیعت).
- خروجی فقط همان JSON باشد؛ هیچ متن دیگری قبل یا بعد از آن ننویس."""


class SlidePlanError(RuntimeError):
    pass


_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text).strip()


def _coerce_layout(value: object) -> str:
    return value if isinstance(value, str) and value in _VALID_LAYOUTS else "bullets-only"


def _coerce_palette(name: object, forced: str | None = None) -> str:
    if forced and forced in PALETTES:
        return forced
    if isinstance(name, str) and name in PALETTES:
        return name
    return DEFAULT_PALETTE


def _normalize_plan(raw: dict, forced_palette: str | None = None) -> dict:
    slides_in = raw.get("slides")
    if not isinstance(slides_in, list) or not slides_in:
        raise SlidePlanError("LLM did not return a valid slides list.")

    slides: list[dict] = []
    for item in slides_in:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        bullets = [str(b).strip() for b in (item.get("bullets") or []) if str(b).strip()][:5]
        slides.append({
            "title": title[:90],
            "layout": _coerce_layout(item.get("layout")),
            "bullets": bullets,
            "needs_image": False,
            "image_prompt": "",
            "speaker_notes": str(item.get("speaker_notes") or "").strip(),
        })

    if not slides:
        raise SlidePlanError("No valid slides remaining after normalization.")

    slides = slides[: settings.presentation_max_slides]
    palette_name = _coerce_palette(raw.get("palette"), forced_palette)
    palette_data = PALETTES[palette_name]

    return {
        "presentation_title": str(raw.get("presentation_title") or "خلاصه کتاب").strip()[:120],
        "subtitle": str(raw.get("subtitle") or "").strip()[:160],
        "palette": palette_name,
        "palette_colors": palette_data,
        "cover_image_prompt": "",
        "slides": slides,
    }


async def build_slide_plan(
    summary_text: str,
    source_filename: str = "",
    forced_palette: str | None = None,
) -> dict:
    """
    Convert a summary into a normalized slide plan dict.
    Retries once with a stricter prompt if the first attempt produces bad JSON.
    """
    system = SYSTEM_PROMPT.replace(
        "__MIN_SLIDES__", str(settings.presentation_min_slides)
    ).replace("__MAX_SLIDES__", str(settings.presentation_max_slides))

    palette_hint = ""
    if forced_palette and forced_palette in PALETTES:
        palette_hint = f'قالب رنگی انتخاب‌شده توسط کاربر: "{forced_palette}" — همین را در فیلد palette برگردان.\n\n'

    prompt = (
        f"{palette_hint}"
        f"نام فایل منبع: {source_filename or 'نامشخص'}\n\n"
        f"متن خلاصه کتاب:\n\n{summary_text}\n\n"
        "حالا طبق فرمت گفته‌شده، فقط JSON طرح اسلایدها را برگردان."
    )

    model = settings.presentation_llm_model or settings.llm_model
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            raw_text = await llm_client.generate(
                prompt,
                system=system,
                model=model,
                max_tokens=settings.presentation_llm_max_tokens,
                temperature=settings.presentation_llm_temperature,
            )
            return _normalize_plan(json.loads(_strip_fences(raw_text)), forced_palette)
        except (json.JSONDecodeError, SlidePlanError) as exc:
            last_error = exc
            logger.warning("Slide plan attempt %s/2 failed: %s", attempt + 1, exc)
            prompt = (
                "خروجی قبلی JSON معتبر نبود. این‌بار **فقط** یک JSON معتبر طبق همان فرمت برگردان، "
                "بدون هیچ متن یا Markdown اضافه.\n\n"
                f"{palette_hint}متن خلاصه کتاب:\n\n{summary_text}"
            )

    raise SlidePlanError(f"Slide plan failed after 2 attempts: {last_error}")
