"""
این ماژول خلاصه‌ی نهایی متن را با کمک LLM به یک ساختار JSON «طرح اسلایدها»
تبدیل می‌کند: تیتر ارائه، پالت رنگی پیشنهادی، و فهرست اسلایدها (هرکدام با
تیتر، بولت‌ها/متن، چیدمان، و در صورت نیاز پرامپت تولید تصویر).

خروجی این ماژول مستقیماً ورودی pptx_builder است.
"""

import json
import logging
import re

from app.config import settings
from app.services import llm_client

logger = logging.getLogger("slide_planner")

# پالت‌های رنگی از پیش تعریف‌شده (هماهنگ با اصول طراحی اسلاید: یک رنگ غالب +
# یک رنگ مکمل + یک accent). نام‌ها دقیقاً همان چیزی هستند که از LLM می‌خواهیم
# انتخاب کند تا به یک مقدار ثابت و معتبر map شوند.
PALETTES: dict[str, dict[str, str]] = {
    "Midnight Executive": {"primary": "1E2761", "secondary": "CADCFC", "accent": "FFFFFF"},
    "Forest & Moss": {"primary": "2C5F2D", "secondary": "97BC62", "accent": "F5F5F5"},
    "Coral Energy": {"primary": "F96167", "secondary": "F9E795", "accent": "2F3C7E"},
    "Warm Terracotta": {"primary": "B85042", "secondary": "E7E8D1", "accent": "A7BEAE"},
    "Ocean Gradient": {"primary": "065A82", "secondary": "1C7293", "accent": "21295C"},
    "Charcoal Minimal": {"primary": "36454F", "secondary": "F2F2F2", "accent": "212121"},
    "Teal Trust": {"primary": "028090", "secondary": "00A896", "accent": "02C39A"},
    "Berry & Cream": {"primary": "6D2E46", "secondary": "A26769", "accent": "ECE2D0"},
    "Sage Calm": {"primary": "84B59F", "secondary": "69A297", "accent": "50808E"},
    "Cherry Bold": {"primary": "990011", "secondary": "FCF6F5", "accent": "2F3C7E"},
}
DEFAULT_PALETTE = "Midnight Executive"

_VALID_LAYOUTS = {"image-right", "image-left", "bullets-only", "quote"}

SYSTEM_PROMPT = """تو یک طراح حرفه‌ای ارائه‌های کلاسی (PowerPoint) هستی که از روی خلاصه‌ی یک کتاب،
ساختار یک ارائه‌ی آموزشی کامل و قابل‌ارائه طراحی می‌کنی.

فقط و فقط یک JSON معتبر (بدون Markdown، بدون توضیح اضافه، بدون ```) با این ساختار دقیق برگردان:

{
  "presentation_title": "عنوان کوتاه و جذاب ارائه (بر اساس موضوع کتاب)",
  "subtitle": "یک زیرعنوان کوتاه (مثلا نام کتاب یا یک جمله توصیفی)",
  "palette": "یکی از این نام‌ها دقیقاً: """ + ", ".join(f'"{name}"' for name in PALETTES) + """",
  "cover_image_prompt": "توصیف تصویری به زبان انگلیسی برای زمینه‌ی اسلاید عنوان، مفهومی و مرتبط با موضوع کلی کتاب، بدون متن/نوشته در تصویر",
  "slides": [
    {
      "title": "تیتر کوتاه اسلاید (حداکثر ۶-۷ کلمه)",
      "layout": "یکی از: image-right, image-left, bullets-only, quote",
      "bullets": ["نکته‌ی کوتاه ۱", "نکته‌ی کوتاه ۲", "نکته‌ی کوتاه ۳"],
      "needs_image": true,
      "image_prompt": "توصیف تصویری به زبان انگلیسی، مناسب برای مدل تصویرساز هوش مصنوعی، بدون متن/نوشته در تصویر",
      "speaker_notes": "یک یا دو جمله توضیح بیشتر برای ارائه‌دهنده (اختیاری)"
    }
  ]
}

قوانین مهم:
- تعداد اسلایدهای محتوایی (فهرست slides) باید بین __MIN_SLIDES__ تا __MAX_SLIDES__ باشد.
- محتوای هر اسلاید باید مستقیماً برگرفته از متن خلاصه باشد؛ چیزی از خودت اضافه نکن.
- هر اسلاید را حول یک ایده/فصل/بخش مشخص از خلاصه بساز تا اسلایدها پوشش کامل و منسجمی از کل خلاصه داشته باشند.
- هر بولت باید کوتاه باشد (حداکثر حدود ۱۴-۱۶ کلمه) تا در یک خط یا دو خط جا شود. هر اسلاید بین ۳ تا ۵ بولت داشته باشد.
- layout را متنوع انتخاب کن (هم image-right هم image-left هم گاهی bullets-only یا quote) تا ارائه یکنواخت نشود.
- needs_image را برای اسلایدهایی که از تصویر بصری/مفهومی سود می‌برند true بگذار (اغلب اسلایدها)؛ برای layout بولت‌خالی (bullets-only) معمولاً false بگذار.
- وقتی needs_image=true است، image_prompt را به زبان انگلیسی و توصیفی بنویس (سبک تصویرسازی/عکاسی مفهومی)، بدون اینکه از مدل بخواهی متن یا نوشته داخل تصویر بگذارد.
- اولین اسلاید باید یک اسلاید مقدمه/کلیات کتاب باشد و آخرین اسلاید باید جمع‌بندی/نتیجه‌گیری باشد.
- خروجی فقط همان JSON باشد؛ هیچ متن دیگری قبل یا بعد از آن ننویس."""


class SlidePlanError(RuntimeError):
    pass


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _coerce_layout(layout: object) -> str:
    if isinstance(layout, str) and layout in _VALID_LAYOUTS:
        return layout
    return "image-right"


def _coerce_palette(name: object) -> str:
    if isinstance(name, str) and name in PALETTES:
        return name
    return DEFAULT_PALETTE


def _normalize_plan(raw: dict) -> dict:
    slides_in = raw.get("slides")
    if not isinstance(slides_in, list) or not slides_in:
        raise SlidePlanError("LLM طرح اسلایدی برنگرداند (فیلد slides خالی/نامعتبر بود).")

    slides: list[dict] = []
    for item in slides_in:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        bullets_raw = item.get("bullets") or []
        bullets = [str(b).strip() for b in bullets_raw if str(b).strip()][:5]

        slides.append(
            {
                "title": title[:90],
                "layout": _coerce_layout(item.get("layout")),
                "bullets": bullets,
                "needs_image": bool(item.get("needs_image")) and bool(
                    str(item.get("image_prompt") or "").strip()
                ),
                "image_prompt": str(item.get("image_prompt") or "").strip(),
                "speaker_notes": str(item.get("speaker_notes") or "").strip(),
            }
        )

    if not slides:
        raise SlidePlanError("هیچ اسلاید معتبری پس از پردازش خروجی LLM باقی نماند.")

    # سقف/کف تعداد اسلاید را اعمال کن (در صورت رعایت‌نشدن توسط مدل)
    slides = slides[: settings.presentation_max_slides]

    presentation_title = str(raw.get("presentation_title") or "خلاصه کتاب").strip()[:120]
    subtitle = str(raw.get("subtitle") or "").strip()[:160]
    palette = _coerce_palette(raw.get("palette"))
    cover_image_prompt = str(raw.get("cover_image_prompt") or "").strip()

    return {
        "presentation_title": presentation_title,
        "subtitle": subtitle,
        "palette": palette,
        "palette_colors": PALETTES[palette],
        "cover_image_prompt": cover_image_prompt,
        "slides": slides,
    }


async def build_slide_plan(summary_text: str, source_filename: str = "") -> dict:
    """
    خلاصه‌ی متن را به یک طرح ساختاریافته‌ی اسلاید (دیکشنری پایتون) تبدیل می‌کند.
    در صورت بد بودن خروجی JSON مدل، یک بار دیگر با یادآوری سخت‌گیرانه‌تر تلاش می‌کند.
    """
    system = SYSTEM_PROMPT.replace(
        "__MIN_SLIDES__", str(settings.presentation_min_slides)
    ).replace("__MAX_SLIDES__", str(settings.presentation_max_slides))
    prompt = (
        f"نام فایل منبع: {source_filename or 'نامشخص'}\n\n"
        f"متن خلاصه کتاب:\n\n{summary_text}\n\n"
        "حالا طبق فرمت گفته‌شده، فقط JSON طرح اسلایدها را برگردان."
    )

    model = settings.presentation_llm_model or settings.llm_model

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            raw_text = await llm_client.generate(prompt, system=system, model=model)
            cleaned = _strip_code_fences(raw_text)
            data = json.loads(cleaned)
            return _normalize_plan(data)
        except (json.JSONDecodeError, SlidePlanError) as exc:
            last_error = exc
            logger.warning("طرح اسلاید نامعتبر بود (تلاش %s/2): %s", attempt + 1, exc)
            prompt = (
                "خروجی قبلی JSON معتبر نبود یا ساختار درستی نداشت. "
                "این‌بار **فقط و فقط** یک JSON معتبر طبق همان فرمت برگردان، "
                "بدون هیچ متن یا Markdown اضافه قبل یا بعد از آن.\n\n"
                f"متن خلاصه کتاب:\n\n{summary_text}"
            )

    raise SlidePlanError(f"ساخت طرح اسلایدها پس از ۲ تلاش ناموفق بود: {last_error}")
