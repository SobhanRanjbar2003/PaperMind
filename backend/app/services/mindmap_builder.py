"""
این ماژول مسئول ساخت Mind Map (نقشه‌ی ذهنی) از روی خلاصه‌ی نهایی و متن خام
کتاب است؛ شبیه قابلیت Mind Map در NotebookLM.

استراتژی دو مرحله‌ای برای کنترل هزینه (تعداد درخواست به LLM):

  مرحله ۱ (۱ درخواست): از روی خلاصه‌ی نهایی، یک درخت با عمق
  `mindmap_first_pass_depth` (پیش‌فرض ۳: ریشه + شاخه‌های اصلی + زیرشاخه)
  ساخته می‌شود. این مرحله ساختار کلی و منسجم را تضمین می‌کند چون خلاصه
  از قبل پاکسازی‌شده و خلاصه‌شده است.

  مرحله ۲ (حداکثر «تعداد شاخه‌های اصلی» درخواست، موازی): برای هر شاخه‌ی
  اصلی (فرزندان مستقیم ریشه)، با کمک متن خام همان بخش از کتاب (chunk های
  مرتبط، نه کل کتاب)، عمق باقی‌مانده تا `mindmap_max_depth` تکمیل می‌شود.
  این مرحله جزئیات دقیق‌تری از متن اصلی (نه فقط خلاصه) به نقشه اضافه می‌کند.

  نتیجه: برای کتابی با N شاخه‌ی اصلی، کل کار با ۱ + N درخواست LLM انجام
  می‌شود؛ نه به تعداد کل chunk های کتاب.

خروجی نهایی هم به شکل درخت تو در تو (مناسب markmap/سلسله‌مراتب) و هم به
شکل مسطح nodes/edges (مناسب React Flow) برگردانده می‌شود.
"""

import asyncio
import json
import logging
import re
import uuid

from app.config import settings
from app.services import llm_client

logger = logging.getLogger("mindmap_builder")


class MindMapError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# پرامپت‌ها
# ---------------------------------------------------------------------------

_FIRST_PASS_SYSTEM_TEMPLATE = """تو یک متخصص ساخت Mind Map (نقشه‌ی ذهنی) از روی خلاصه‌ی کتاب هستی،
دقیقاً شبیه قابلیت Mind Map ابزار NotebookLM.

از روی خلاصه‌ی کتابی که در ادامه می‌آید، یک نقشه‌ی ذهنی درختی بساز:
- یک گره ریشه (موضوع کلی کتاب).
- زیرمجموعه‌های ریشه: مهم‌ترین شاخه‌ها/فصل‌ها/محورهای اصلی کتاب.
- زیرمجموعه‌ی هر شاخه‌ی اصلی: نکات مهم‌تر و جزئی‌تر آن شاخه.

قوانین مهم:
- عمق این درخت باید دقیقاً {first_pass_depth} سطح باشد (ریشه = سطح ۱).
- هر گره حداکثر {max_children} فرزند داشته باشد؛ تعداد فرزندان را بر اساس نیاز واقعی موضوع انتخاب کن (لازم نیست همیشه دقیقاً {max_children} باشد)، اما هرگز بیشتر از آن نباشد.
- برچسب (label) هر گره باید کوتاه باشد: فقط یک عبارت کلیدی یا چند کلمه (حداکثر حدود ۸-۱۰ کلمه)، نه یک جمله‌ی کامل. این برچسب باید بتواند داخل یک باکس کوچک در نمودار جا شود.
- هرچه عمق بیشتر می‌شود، نکات باید جزئی‌تر و دقیق‌تر شوند (نه تکرار سطح بالاتر با کلمات دیگر).
- از تکرار یک مضمون در چند شاخه‌ی مختلف خودداری کن؛ هر شاخه باید بخش متمایزی از محتوا را پوشش دهد.
- محتوا باید مستقیماً برگرفته از خلاصه باشد؛ چیزی از خودت اضافه نکن یا حدس نزن.
- خروجی فقط و فقط یک JSON معتبر باشد (بدون Markdown، بدون ```، بدون هیچ توضیح قبل یا بعد) با این ساختار دقیق:

{{
  "label": "عنوان کلی کتاب/موضوع (ریشه)",
  "children": [
    {{
      "label": "عنوان شاخه‌ی اصلی ۱",
      "children": [
        {{"label": "نکته‌ی جزئی‌تر ۱.۱", "children": []}},
        {{"label": "نکته‌ی جزئی‌تر ۱.۲", "children": []}}
      ]
    }}
  ]
}}

نکته: چون عمق درخواستی {first_pass_depth} سطح است، فیلد "children" در عمیق‌ترین سطح باید آرایه‌ی خالی [] باشد (در همین مرحله چیز عمیق‌تری نساز؛ آن کار در مرحله‌ی بعد انجام می‌شود)."""

_EXPAND_SYSTEM_TEMPLATE = """تو یک متخصص ساخت Mind Map (نقشه‌ی ذهنی) هستی. در ادامه یک «شاخه»ی از یک
نقشه‌ی ذهنی بزرگ‌تر (مربوط به یک کتاب) به همراه متن خام همان بخش از کتاب آمده
است. وظیفه‌ی تو این است که این شاخه را عمیق‌تر و دقیق‌تر کنی؛ یعنی برای
برگ‌های (deepest leaves) فعلی این زیردرخت، زیرشاخه‌های جزئی‌تر بر اساس متن خام
اضافه کنی (نه بر اساس حدس، بلکه بر اساس جزئیاتی که واقعاً در متن خام هست).

قوانین مهم:
- ساختار فعلی شاخه (که در ادامه به صورت JSON آمده) را باید دقیقاً حفظ کنی؛ فقط
  به عمیق‌ترین سطح فعلی (جایی که "children" خالی [] است) زیرشاخه‌ی جدید اضافه کن.
- مجموع عمق تا پایین‌ترین برگ جدید باید حداکثر {remaining_depth} سطح بیشتر از
  عمق فعلی باشد (یعنی نباید بیشتر از {remaining_depth} سطح جدید اضافه شود).
- هر گره حداکثر {max_children} فرزند داشته باشد.
- برچسب هر گره جدید کوتاه باشد (حداکثر ۸-۱۰ کلمه)، نه جمله‌ی کامل.
- زیرشاخه‌های جدید باید جزئیات دقیق، مثال‌های واقعی، اسامی، اعداد، یا نکات
  ریزی باشند که در متن خام آمده ولی در خلاصه‌ی کلی نبوده یا کوتاه شده بود.
- اگر متن خام برای عمیق‌تر کردن بخشی از این شاخه کافی نیست، همان گره را بدون
  فرزند جدید (children خالی) رها کن؛ چیزی از خودت حدس نزن یا اضافه نکن.
- خروجی فقط و فقط همان ساختار JSON «شاخه» (با همان فیلدهای label/children) باشد؛
  بدون Markdown، بدون ```، بدون هیچ توضیح اضافه قبل یا بعد."""


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _coerce_label(value: object, fallback: str = "بدون عنوان") -> str:
    label = str(value or "").strip()
    if not label:
        return fallback
    # برچسب باید کوتاه باشد؛ اگر مدل جمله‌ی بلند برگرداند، بریده می‌شود.
    return label[:120]


def _normalize_node(raw: object, max_children: int) -> dict:
    """یک نود خام (dict از خروجی JSON مدل) را اعتبارسنجی و نرمال می‌کند."""
    if not isinstance(raw, dict):
        return {"label": _coerce_label(raw), "children": []}

    label = _coerce_label(raw.get("label") or raw.get("title") or raw.get("text"))
    children_raw = raw.get("children")
    children: list[dict] = []
    if isinstance(children_raw, list):
        for child in children_raw[:max_children]:
            children.append(_normalize_node(child, max_children))

    return {"label": label, "children": children}


def _tree_depth(node: dict) -> int:
    if not node.get("children"):
        return 1
    return 1 + max(_tree_depth(c) for c in node["children"])


def _collect_leaves(node: dict, path: list[dict] | None = None) -> list[list[dict]]:
    """تمام مسیرهای ریشه‌تا‌برگ را برمی‌گرداند (هر مسیر = لیست نودهای از ریشه تا برگ)."""
    path = (path or []) + [node]
    if not node.get("children"):
        return [path]
    leaves: list[list[dict]] = []
    for child in node["children"]:
        leaves.extend(_collect_leaves(child, path))
    return leaves


# ---------------------------------------------------------------------------
# مرحله ۱: ساخت ساختار کلی از روی خلاصه
# ---------------------------------------------------------------------------


async def build_first_pass(summary_text: str) -> dict:
    """
    از روی خلاصه‌ی نهایی، درخت اولیه (ریشه + شاخه‌های اصلی + یک سطح زیرشاخه)
    را می‌سازد. در صورت JSON نامعتبر، یک بار دیگر با یادآوری سخت‌گیرانه‌تر
    تلاش می‌کند.
    """
    first_pass_depth = max(settings.mindmap_first_pass_depth, 2)
    system = _FIRST_PASS_SYSTEM_TEMPLATE.format(
        first_pass_depth=first_pass_depth,
        max_children=settings.mindmap_max_children,
    )
    prompt = (
        f"خلاصه‌ی کتاب:\n\n{summary_text}\n\n"
        "حالا طبق فرمت گفته‌شده، فقط JSON نقشه‌ی ذهنی را برگردان."
    )

    model = settings.mindmap_llm_model or settings.llm_model

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            raw_text = await llm_client.generate(
                prompt,
                system=system,
                model=model,
            )
            cleaned = _strip_code_fences(raw_text)
            data = json.loads(cleaned)
            node = _normalize_node(data, settings.mindmap_max_children)
            if not node["children"]:
                raise MindMapError("مدل هیچ شاخه‌ی اصلی‌ای برای نقشه‌ی ذهنی برنگرداند.")
            return node
        except (json.JSONDecodeError, MindMapError) as exc:
            last_error = exc
            logger.warning(
                "ساختار اولیه‌ی mind map نامعتبر بود (تلاش %s/2): %s", attempt + 1, exc
            )
            prompt = (
                "خروجی قبلی JSON معتبر نبود یا ساختار درستی نداشت. این‌بار **فقط و فقط** "
                "یک JSON معتبر طبق همان فرمت برگردان، بدون هیچ متن یا Markdown اضافه.\n\n"
                f"خلاصه‌ی کتاب:\n\n{summary_text}"
            )

    raise MindMapError(f"ساخت ساختار اولیه‌ی mind map پس از ۲ تلاش ناموفق بود: {last_error}")


# ---------------------------------------------------------------------------
# مرحله ۲: تعمیق هر شاخه‌ی اصلی با کمک متن خام chunk های مرتبط
# ---------------------------------------------------------------------------


def _select_branch_context(branch_label: str, chunks: list[str], branch_index: int, total_branches: int) -> str:
    """
    متن خام مرتبط با یک شاخه را انتخاب می‌کند.

    برای جلوگیری از یک درخواست LLM جدا برای matching (که هزینه‌ی اضافه دارد)،
    یک تخمین ساده و رایگان استفاده می‌شود: کتاب معمولاً به ترتیب خوانده/خلاصه
    می‌شود، پس شاخه‌ی i-ام از N شاخه‌ی اصلی تقریباً به بخش i-ام از chunk های
    کتاب (به ترتیب) مربوط است. این تخمین دقیق نیست ولی برای «غنی‌سازی با
    جزئیات واقعی متن» کافی است و هیچ هزینه‌ی LLM اضافه‌ای ندارد.
    """
    if not chunks:
        return ""

    n = len(chunks)
    start_idx = (branch_index * n) // total_branches
    end_idx = ((branch_index + 1) * n) // total_branches
    end_idx = max(end_idx, start_idx + 1)
    relevant = chunks[start_idx:end_idx]

    combined = "\n\n".join(relevant)
    limit = settings.mindmap_branch_context_chars
    if len(combined) > limit:
        # از وسط بخش مرتبط برش می‌زنیم تا هم ابتدا هم انتهای آن حفظ شود
        half = limit // 2
        combined = combined[:half] + "\n...\n" + combined[-half:]
    return combined


async def _expand_branch(branch: dict, branch_context: str, current_depth: int) -> dict:
    """یک شاخه‌ی اصلی (با زیردرخت فعلی‌اش) را با کمک متن خام عمیق‌تر می‌کند."""
    remaining_depth = settings.mindmap_max_depth - current_depth
    if remaining_depth <= 0 or not branch_context.strip():
        return branch

    system = _EXPAND_SYSTEM_TEMPLATE.format(
        remaining_depth=remaining_depth,
        max_children=settings.mindmap_max_children,
    )
    prompt = (
        f"ساختار فعلی این شاخه (JSON):\n\n{json.dumps(branch, ensure_ascii=False)}\n\n"
        f"متن خام مرتبط با این بخش از کتاب:\n\n{branch_context}\n\n"
        "حالا همین ساختار را با زیرشاخه‌های جدید در عمیق‌ترین سطح، عمیق‌تر کن و فقط JSON آن را برگردان."
    )

    model = settings.mindmap_llm_model or settings.llm_model

    try:
        raw_text = await llm_client.generate(prompt, system=system, model=model)
        cleaned = _strip_code_fences(raw_text)
        data = json.loads(cleaned)
        expanded = _normalize_node(data, settings.mindmap_max_children)
        # اگر مدل برچسب ریشه‌ی شاخه را عوض کرد یا ساختار را خراب کرد، برچسب اصلی را نگه می‌داریم
        if not expanded.get("label"):
            expanded["label"] = branch["label"]
        return expanded
    except (json.JSONDecodeError, MindMapError) as exc:
        logger.warning(
            "تعمیق شاخه '%s' ناموفق بود؛ همان شاخه‌ی اولیه (بدون عمق بیشتر) نگه داشته می‌شود: %s",
            branch.get("label"),
            exc,
        )
        return branch


async def expand_branches(
    root: dict,
    chunks: list[str],
    on_branch_done=None,
) -> dict:
    """
    تمام شاخه‌های اصلی (فرزندان مستقیم ریشه) را به صورت موازی (با سقف
    هم‌زمانی `mindmap_expand_max_concurrency`) با کمک متن خام chunk های
    مرتبط عمیق‌تر می‌کند.
    """
    branches = root.get("children") or []
    if not branches:
        return root

    current_depth = settings.mindmap_first_pass_depth
    semaphore = asyncio.Semaphore(settings.mindmap_expand_max_concurrency)
    total = len(branches)

    async def _run(idx: int, branch: dict) -> dict:
        async with semaphore:
            context = _select_branch_context(branch["label"], chunks, idx, total)
            result = await _expand_branch(branch, context, current_depth)
        if on_branch_done is not None:
            on_branch_done()
        return result

    expanded_branches = await asyncio.gather(
        *[_run(idx, branch) for idx, branch in enumerate(branches)]
    )
    root["children"] = list(expanded_branches)
    return root


# ---------------------------------------------------------------------------
# تبدیل درخت نهایی به فرمت‌های قابل مصرف فرانت (tree با id + nodes/edges مسطح)
# ---------------------------------------------------------------------------


def assign_ids_and_flatten(root: dict, max_depth: int) -> tuple[dict, list[dict], list[dict]]:
    """
    به هر نود یک id یکتا می‌دهد، عمق هر نود را ست می‌کند، عمق درخت را به
    `max_depth` محدود می‌کند (برگ‌های عمیق‌تر حذف می‌شوند)، و در نهایت هم
    نسخه‌ی درختی (با id) و هم نسخه‌ی مسطح nodes/edges را برمی‌گرداند.
    """
    nodes: list[dict] = []
    edges: list[dict] = []

    def _walk(node: dict, depth: int, parent_id: str | None) -> dict | None:
        if depth >= max_depth:
            return None

        node_id = str(uuid.uuid4())[:8]
        tree_node = {
            "id": node_id,
            "label": node["label"],
            "depth": depth,
            "children": [],
        }
        nodes.append(
            {
                "id": node_id,
                "label": node["label"],
                "depth": depth,
                "parent_id": parent_id,
            }
        )
        if parent_id is not None:
            edges.append(
                {
                    "id": f"e-{parent_id}-{node_id}",
                    "source": parent_id,
                    "target": node_id,
                }
            )

        for child in node.get("children") or []:
            child_tree = _walk(child, depth + 1, node_id)
            if child_tree is not None:
                tree_node["children"].append(child_tree)

        return tree_node

    tree = _walk(root, 0, None)
    if tree is None:
        # نباید اتفاق بیفتد چون ریشه همیشه در عمق ۰ است، ولی برای ایمنی:
        tree = {"id": str(uuid.uuid4())[:8], "label": root.get("label", ""), "depth": 0, "children": []}
        nodes = [{"id": tree["id"], "label": tree["label"], "depth": 0, "parent_id": None}]
        edges = []

    return tree, nodes, edges
