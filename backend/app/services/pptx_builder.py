"""
ساخت فایل نهایی PowerPoint (.pptx) از روی «طرح اسلاید» (خروجی slide_planner)
و تصاویر تولیدشده (خروجی image_client).

نکات طراحی رعایت‌شده:
- پشتیبانی کامل از راست‌به‌چپ (RTL) برای متن فارسی (هم alignment و هم پرچم rtl
  در XML پاراگراف‌ها، هم فونت complex-script).
- یک پالت رنگی غالب با ۱-۲ رنگ مکمل و یک accent (نه رنگ‌های هم‌وزن).
- یک motif بصری تکرارشونده در کل ارائه: دایره‌های شماره‌دار کنار هر بولت.
- تصاویر half-bleed (تمام-عرض/ارتفاع) با crop مناسب (بدون کشیدگی تصویر).
- تنوع چیدمان بین اسلایدها (image-right / image-left / bullets-only / quote).
- اگر تصویر یک اسلاید موجود نبود، به‌جای فضای خالی، یک shape تزئینی جایگزین می‌شود.
"""

import io
import logging

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from app.config import settings

logger = logging.getLogger("pptx_builder")

MARGIN = Inches(0.6)
GAP = Inches(0.45)
IMG_COL_W = Inches(5.1)

FONT_FA = settings.presentation_font_fa


# ---------------------------------------------------------------------------
# توابع کمکی پایه (رنگ، فونت، RTL)
# ---------------------------------------------------------------------------

def _rgb(hex_str: str) -> RGBColor:
    return RGBColor.from_string(hex_str)


def _luminance(hex_str: str) -> float:
    r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _contrast_text(bg_hex: str) -> str:
    """رنگ متن (سفید یا تیره) با کنتراست مناسب روی پس‌زمینه‌ی داده‌شده."""
    return "FFFFFF" if _luminance(bg_hex) < 150 else "1A1A1A"


def _best_text_color(bg_hex: str, preferred_hex: str, min_diff: float = 90.0) -> str:
    """
    اگر preferred_hex (مثلا رنگ secondary/accent پالت) روی bg_hex کنتراست کافی
    داشت همان را برمی‌گرداند؛ وگرنه به یک سفید/تیره‌ی امن fallback می‌کند.
    این از مشکل متن کم‌کنتراست در پالت‌هایی که رنگ‌هایشان به‌هم نزدیک‌اند جلوگیری می‌کند.
    """
    if abs(_luminance(bg_hex) - _luminance(preferred_hex)) >= min_diff:
        return preferred_hex
    return "F2F2F2" if _luminance(bg_hex) < 150 else "1A1A1A"


def _pick_contrasting(bg_hex: str, candidates: list[str], min_diff: float = 70.0) -> str:
    """اولین رنگ از candidates که نسبت به bg_hex کنتراست کافی دارد را برمی‌گرداند."""
    for candidate in candidates:
        if abs(_luminance(bg_hex) - _luminance(candidate)) >= min_diff:
            return candidate
    return "F2F2F2" if _luminance(bg_hex) < 150 else "1A1A1A"


def _set_rtl(paragraph) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("rtl", "1")


def _style_run(run, size_pt: float, color_hex: str, bold: bool = False, italic: bool = False) -> None:
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = _rgb(color_hex)
    run.font.name = FONT_FA

    # برای رندر صحیح گلیف‌های فارسی/عربی، فونت complex-script (a:cs) و
    # east-asian (a:ea) را هم صریحاً ست می‌کنیم؛ صرفاً a:latin کافی نیست.
    rPr = run._r.get_or_add_rPr()
    for tag, successors in (
        ("a:ea", ("a:cs", "a:sym", "a:hlinkClick", "a:hlinkMouseOver", "a:rtl", "a:extLst")),
        ("a:cs", ("a:sym", "a:hlinkClick", "a:hlinkMouseOver", "a:rtl", "a:extLst")),
    ):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.insert_element_before(el, *successors)
        el.set("typeface", FONT_FA)


def _set_alpha(shape, alpha_pct: int) -> None:
    """شفافیت یک shape با fill تخت را تنظیم می‌کند (alpha_pct بین 0 تا 100)."""
    solidFill = shape.fill.fore_color._xFill
    srgbClr = solidFill.find(qn("a:srgbClr"))
    if srgbClr is not None:
        alpha = srgbClr.makeelement(qn("a:alpha"), {})
        alpha.set("val", str(int(alpha_pct * 1000)))
        srgbClr.append(alpha)


def _no_line(shape) -> None:
    shape.line.fill.background()
    try:
        shape.shadow.inherit = False
    except Exception:  # noqa: BLE001  - برخی shapeها shadow ندارند
        pass


def _solid(shape, hex_color: str, alpha_pct: int | None = None) -> None:
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(hex_color)
    if alpha_pct is not None and alpha_pct < 100:
        _set_alpha(shape, alpha_pct)


def _set_bg(slide, hex_color: str) -> None:
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(hex_color)


def _textbox(slide, left, top, width, height):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    return tb, tf


# ---------------------------------------------------------------------------
# تصویر: درج با برش "cover" (بدون کشیدگی، بدون فضای خالی اطراف)
# ---------------------------------------------------------------------------

def _add_cover_image(slide, image_bytes: bytes, left, top, width, height):
    stream = io.BytesIO(image_bytes)
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            iw, ih = img.size
    except Exception:  # noqa: BLE001
        iw, ih = 1, 1

    pic = slide.shapes.add_picture(stream, left, top, width=width, height=height)

    if iw <= 0 or ih <= 0:
        return pic

    img_ratio = iw / ih
    box_ratio = width / height

    if img_ratio > box_ratio:
        crop = max(0.0, min(0.49, (1 - box_ratio / img_ratio) / 2))
        pic.crop_left = crop
        pic.crop_right = crop
    elif img_ratio < box_ratio:
        crop = max(0.0, min(0.49, (1 - img_ratio / box_ratio) / 2))
        pic.crop_top = crop
        pic.crop_bottom = crop

    return pic


def _add_decorative_motif(slide, x_anchor, y_anchor, color_a: str, color_b: str, scale: float = 1.0) -> None:
    """در نبود تصویر (یا برای زینت اسلاید عنوان/پایان)، چند دایره هم‌پوشان رسم می‌کند."""
    d1 = Inches(3.2 * scale)
    d2 = Inches(2.0 * scale)
    c1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, x_anchor - d1 // 2, y_anchor - d1 // 2, d1, d1)
    _solid(c1, color_a, alpha_pct=22)
    _no_line(c1)
    c2 = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, x_anchor - d2 // 2 + Inches(0.6 * scale), y_anchor - d2 // 2 + Inches(0.4 * scale), d2, d2
    )
    _solid(c2, color_b, alpha_pct=35)
    _no_line(c2)


# ---------------------------------------------------------------------------
# motif اصلی: ردیف‌های «دایره‌ی شماره‌دار + متن» برای بولت‌ها
# ---------------------------------------------------------------------------

def _add_bullet_rows(
    slide,
    bullets: list[str],
    x,
    y,
    width,
    height,
    circle_color: str,
    text_color: str,
    font_size: float = 16,
) -> None:
    n = len(bullets)
    if n == 0:
        return

    ideal_row_h = Inches(1.3)
    row_h = Emu(min(int(ideal_row_h), int(height / n)))
    total_h = Emu(int(row_h * n))
    y = Emu(int(y + max(0, (height - total_h) / 2)))

    circle_d = Inches(0.5)
    gap_circle_text = Inches(0.18)

    for i, bullet in enumerate(bullets):
        row_top = Emu(int(y + i * row_h))

        circle_left = Emu(int(x + width - circle_d))
        circle_top = Emu(int(row_top + (row_h - circle_d) / 2))
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, circle_left, circle_top, circle_d, circle_d)
        _solid(circle, circle_color)
        _no_line(circle)
        ctf = circle.text_frame
        ctf.word_wrap = False
        ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0
        cp = ctf.paragraphs[0]
        cp.alignment = PP_ALIGN.CENTER
        crun = cp.add_run()
        crun.text = str(i + 1)
        _style_run(crun, 15, _contrast_text(circle_color), bold=True)

        text_w = Emu(int(width - circle_d - gap_circle_text))
        _tb, tf = _textbox(slide, x, row_top, text_w, row_h)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        _set_rtl(p)
        run = p.add_run()
        run.text = bullet
        _style_run(run, font_size, text_color)


# ---------------------------------------------------------------------------
# اسلاید عنوان
# ---------------------------------------------------------------------------

def _add_title_slide(prs, layout, plan: dict, cover_image: bytes | None, primary: str, secondary: str, accent: str) -> None:
    slide = prs.slides.add_slide(layout)
    sw, sh = prs.slide_width, prs.slide_height

    if cover_image:
        _add_cover_image(slide, cover_image, 0, 0, sw, sh)
        overlay = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, sw, sh)
        _solid(overlay, primary, alpha_pct=72)
        _no_line(overlay)
    else:
        _set_bg(slide, primary)
        _add_decorative_motif(slide, sw - Inches(2.2), sh - Inches(1.8), secondary, accent, scale=1.3)
        _add_decorative_motif(slide, Inches(1.4), Inches(1.2), accent, secondary, scale=0.8)

    title_text_color = "FFFFFF" if _luminance(primary) < 150 else "1A1A1A"

    _tb, tf = _textbox(slide, Inches(1.0), sh / 2 - Inches(1.1), sw - Inches(2.0), Inches(1.6))
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _set_rtl(p)
    run = p.add_run()
    run.text = plan["presentation_title"]
    _style_run(run, 44, title_text_color, bold=True)

    if plan.get("subtitle"):
        _tb2, tf2 = _textbox(slide, Inches(1.5), sh / 2 + Inches(0.55), sw - Inches(3.0), Inches(0.9))
        p2 = tf2.paragraphs[0]
        p2.alignment = PP_ALIGN.CENTER
        _set_rtl(p2)
        run2 = p2.add_run()
        run2.text = plan["subtitle"]
        _style_run(run2, 20, _best_text_color(primary, secondary))


# ---------------------------------------------------------------------------
# اسلایدهای محتوایی
# ---------------------------------------------------------------------------

def _add_content_title(slide, x, width, text: str, color: str) -> Emu:
    top = Inches(0.55)
    height = Inches(1.15)
    _tb, tf = _textbox(slide, x, top, width, height)
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _set_rtl(p)
    run = p.add_run()
    run.text = text
    _style_run(run, 32, color, bold=True)
    return Emu(int(top + height))


def _add_image_variant_slide(
    prs, layout, slide_data: dict, primary: str, secondary: str, accent: str, image_bytes: bytes | None, image_left: bool
) -> None:
    slide = prs.slides.add_slide(layout)
    sw, sh = prs.slide_width, prs.slide_height
    _set_bg(slide, "FFFFFF")

    if image_left:
        img_x = 0
        text_x = Emu(int(IMG_COL_W + GAP))
    else:
        img_x = Emu(int(sw - IMG_COL_W))
        text_x = MARGIN

    text_w = Emu(int(sw - IMG_COL_W - GAP - MARGIN))

    if image_bytes:
        _add_cover_image(slide, image_bytes, img_x, 0, IMG_COL_W, sh)
    else:
        # نبود تصویر: shape تزئینی جایگزین به‌جای فضای خالی
        block = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, img_x, 0, IMG_COL_W, sh)
        _solid(block, secondary, alpha_pct=100)
        _no_line(block)
        cx = Emu(int(img_x + IMG_COL_W / 2))
        _add_decorative_motif(slide, cx, Emu(int(sh / 2)), primary, accent, scale=1.1)

    title_bottom = _add_content_title(slide, text_x, text_w, slide_data["title"], "1A1A1A")

    bullets_top = Emu(int(title_bottom + Inches(0.25)))
    bullets_height = Emu(int(sh - bullets_top - Inches(0.55)))
    _add_bullet_rows(
        slide,
        slide_data["bullets"],
        text_x,
        bullets_top,
        text_w,
        bullets_height,
        circle_color=primary,
        text_color="2B2B2B",
        font_size=16,
    )

    _add_speaker_notes(slide, slide_data)


def _add_bullets_only_slide(prs, layout, slide_data: dict, primary: str, secondary: str, accent: str) -> None:
    slide = prs.slides.add_slide(layout)
    sw, sh = prs.slide_width, prs.slide_height
    _set_bg(slide, "FFFFFF")

    content_x = MARGIN
    content_w = Emu(int(sw - 2 * MARGIN))

    title_bottom = _add_content_title(slide, content_x, content_w, slide_data["title"], "1A1A1A")

    bullets_top = Emu(int(title_bottom + Inches(0.35)))
    bullets_height = Emu(int(sh - bullets_top - Inches(0.6)))
    bullets_w = Emu(int(content_w * 0.62))
    bullets_x = Emu(int(content_x + (content_w - bullets_w) / 2))

    _add_bullet_rows(
        slide,
        slide_data["bullets"],
        bullets_x,
        bullets_top,
        bullets_w,
        bullets_height,
        circle_color=primary,
        text_color="2B2B2B",
        font_size=18,
    )

    _add_speaker_notes(slide, slide_data)


def _add_quote_slide(prs, layout, slide_data: dict, primary: str, secondary: str, accent: str) -> None:
    slide = prs.slides.add_slide(layout)
    sw, sh = prs.slide_width, prs.slide_height
    _set_bg(slide, primary)
    _add_decorative_motif(slide, Inches(1.3), sh - Inches(1.2), accent, secondary, scale=1.0)
    _add_decorative_motif(slide, sw - Inches(1.3), Inches(1.2), secondary, accent, scale=0.9)

    text_color = "FFFFFF" if _luminance(primary) < 150 else "1A1A1A"
    quote_text = (slide_data.get("bullets") or [slide_data["title"]])[0]

    _tb, tf = _textbox(slide, Inches(1.6), sh / 2 - Inches(1.3), sw - Inches(3.2), Inches(2.0))
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _set_rtl(p)
    run = p.add_run()
    run.text = quote_text
    _style_run(run, 30, text_color, italic=True, bold=False)

    _tb2, tf2 = _textbox(slide, Inches(2.0), sh / 2 + Inches(1.0), sw - Inches(4.0), Inches(0.8))
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    _set_rtl(p2)
    run2 = p2.add_run()
    run2.text = slide_data["title"]
    _style_run(run2, 18, _best_text_color(primary, accent), bold=True)

    _add_speaker_notes(slide, slide_data)


def _add_speaker_notes(slide, slide_data: dict) -> None:
    notes = slide_data.get("speaker_notes")
    if notes:
        slide.notes_slide.notes_text_frame.text = notes


# ---------------------------------------------------------------------------
# اسلاید پایانی (جمع‌بندی)
# ---------------------------------------------------------------------------

def _add_closing_slide(prs, layout, plan: dict, primary: str, secondary: str, accent: str) -> None:
    slide = prs.slides.add_slide(layout)
    sw, sh = prs.slide_width, prs.slide_height
    _set_bg(slide, primary)
    _add_decorative_motif(slide, sw - Inches(2.0), Inches(1.5), secondary, accent, scale=1.2)

    text_color = "FFFFFF" if _luminance(primary) < 150 else "1A1A1A"

    _tb, tf = _textbox(slide, Inches(1.0), Inches(0.9), sw - Inches(2.0), Inches(1.0))
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _set_rtl(p)
    run = p.add_run()
    run.text = "جمع‌بندی"
    _style_run(run, 38, text_color, bold=True)

    recap_titles = [s["title"] for s in plan["slides"][:6]]
    bullets_w = Emu(int((sw - Inches(2.0)) * 0.8))
    bullets_x = Emu(int(Inches(1.0) + ((sw - Inches(2.0)) - bullets_w) / 2))
    bullets_top = Inches(2.1)
    bullets_h = Emu(int(sh - bullets_top - Inches(1.1)))

    _add_bullet_rows(
        slide,
        recap_titles,
        bullets_x,
        bullets_top,
        bullets_w,
        bullets_h,
        circle_color=_pick_contrasting(primary, [secondary, accent]),
        text_color=text_color,
        font_size=18,
    )

    _tb2, tf2 = _textbox(slide, Inches(1.5), sh - Inches(0.9), sw - Inches(3.0), Inches(0.6))
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    _set_rtl(p2)
    run2 = p2.add_run()
    run2.text = f"پایان ارائه — بر اساس خلاصه‌ی «{plan['presentation_title']}»"
    _style_run(run2, 14, _best_text_color(primary, accent), italic=True)


# ---------------------------------------------------------------------------
# تابع اصلی
# ---------------------------------------------------------------------------

def build_presentation(
    plan: dict,
    slide_images: dict[int, bytes],
    cover_image: bytes | None,
    output_path: str,
) -> str:
    """
    فایل pptx نهایی را می‌سازد و در output_path ذخیره می‌کند.

    - plan: خروجی normalize‌شده‌ی slide_planner.build_slide_plan
    - slide_images: دیکشنری {index اسلاید در plan['slides']: bytes تصویر}
    - cover_image: بایت‌های تصویر زمینه‌ی اسلاید عنوان (یا None)
    """
    prs = Presentation()
    prs.slide_width = Inches(settings.presentation_slide_width_in)
    prs.slide_height = Inches(settings.presentation_slide_height_in)
    layout = prs.slide_layouts[6]  # layout کاملاً خالی (بدون placeholder)

    colors = plan["palette_colors"]
    primary, secondary, accent = colors["primary"], colors["secondary"], colors["accent"]

    prs.core_properties.title = plan["presentation_title"]
    prs.core_properties.author = "Book Summarizer"

    _add_title_slide(prs, layout, plan, cover_image, primary, secondary, accent)

    for idx, slide_data in enumerate(plan["slides"]):
        image_bytes = slide_images.get(idx)
        layout_kind = slide_data["layout"]

        if layout_kind == "image-right":
            _add_image_variant_slide(prs, layout, slide_data, primary, secondary, accent, image_bytes, image_left=False)
        elif layout_kind == "image-left":
            _add_image_variant_slide(prs, layout, slide_data, primary, secondary, accent, image_bytes, image_left=True)
        elif layout_kind == "quote":
            _add_quote_slide(prs, layout, slide_data, primary, secondary, accent)
        else:  # bullets-only یا هر مقدار ناشناخته
            _add_bullets_only_slide(prs, layout, slide_data, primary, secondary, accent)

    _add_closing_slide(prs, layout, plan, primary, secondary, accent)

    prs.save(output_path)
    logger.info("فایل پاورپوینت ساخته شد: %s", output_path)
    return output_path
