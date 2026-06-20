"""
کلاینت اتصال به API تولید تصویر (مدل تصویرساز روی سرور آروان، مثلا
Gemini-3-1-Flash-Lite-Preview-ax1s0).

این ماژول کاملاً مستقل از llm_client متنی است چون معمولاً سرویس تصویرسازی
endpoint/کلید جدا و قرارداد پاسخ متفاوتی دارد. سه «سبک» رایج پشتیبانی می‌شود
(قابل انتخاب با IMAGE_REQUEST_STYLE در .env):

  - openai_images          : POST {base}/images/generations  (رایج‌ترین حالت)
  - openai_chat_multimodal : POST {base}/chat/completions با خروجی تصویر در پیام
  - gemini                 : POST {base}/models/{model}:generateContent

⚠️ نکته مهم: چون قرارداد دقیق API سرور آروان برای این مدل خاص مستند رسمی
عمومی ندارد، پیش‌فرض روی متداول‌ترین حالت (openai_images) تنظیم شده و
parser پاسخ هم چند ساختار رایج را امتحان می‌کند. اگر سرور شما فرمت دیگری
برمی‌گرداند، کافی‌ست تابع `_build_payload` و `_extract_image_b64` را با
نمونه پاسخ واقعی سرورتان تطبیق دهید (به README بخش «تولید تصویر» نگاه کنید).
"""

import asyncio
import base64
import logging

import httpx

from app.config import settings

logger = logging.getLogger("image_client")

_semaphore = asyncio.Semaphore(settings.image_max_concurrency)
_client: httpx.AsyncClient | None = None

_RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.image_base_url,
            timeout=settings.image_request_timeout,
            headers={
                "Authorization": f"apikey {settings.image_api_key}",
                "Content-Type": "application/json",
            },
            limits=httpx.Limits(
                max_connections=settings.image_max_concurrency * 2,
                max_keepalive_connections=settings.image_max_concurrency,
            ),
        )
    return _client


async def aclose_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _build_request(prompt: str) -> tuple[str, dict]:
    """بر اساس IMAGE_REQUEST_STYLE، مسیر endpoint و payload مناسب را می‌سازد."""
    style = settings.image_request_style

    if style == "gemini":
        path = f"/models/{settings.image_model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        return path, payload

    if style == "openai_chat_multimodal":
        path = "/chat/completions"
        payload = {
            "model": settings.image_model,
            "messages": [{"role": "user", "content": prompt}],
        }
        return path, payload

    # پیش‌فرض: openai_images
    path = settings.image_endpoint_path
    payload = {
        "model": settings.image_model,
        "prompt": prompt,
        "n": 1,
        "size": settings.image_size,
        "response_format": "b64_json",
    }
    return path, payload


def _extract_image_b64(data: dict) -> str:
    """
    تلاش می‌کند تصویر base64 را از چند ساختار رایج پاسخ استخراج کند.
    اگر پاسخ سرور شما با هیچ‌کدام مطابقت نداشت، این تابع را با ساختار
    واقعی پاسخ سرورتان تطبیق دهید.
    """
    # ساختار OpenAI-style images API: {"data": [{"b64_json": "..."}]}
    if isinstance(data.get("data"), list) and data["data"]:
        item = data["data"][0]
        if item.get("b64_json"):
            return item["b64_json"]
        if item.get("url"):
            raise _NeedsUrlDownload(item["url"])

    # ساختار chat-completions با خروجی چندرسانه‌ای:
    # {"choices": [{"message": {"images": [{"image_url": {"url": "data:image/png;base64,..."}}]}}]}
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") or {}
        images = message.get("images")
        if isinstance(images, list) and images:
            url = (images[0].get("image_url") or {}).get("url", "")
            if url.startswith("data:") and "base64," in url:
                return url.split("base64,", 1)[1]
            if url:
                raise _NeedsUrlDownload(url)
        content = message.get("content")
        if isinstance(content, str) and content.startswith("data:") and "base64," in content:
            return content.split("base64,", 1)[1]

    # ساختار Gemini-style: {"candidates": [{"content": {"parts": [{"inlineData": {"data": "..."}}]}}]}
    candidates = data.get("candidates")
    if isinstance(candidates, list) and candidates:
        parts = ((candidates[0].get("content") or {}).get("parts")) or []
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return inline["data"]

    raise RuntimeError(f"ساختار پاسخ API تصویرسازی شناخته‌شده نبود: {str(data)[:500]}")


class _NeedsUrlDownload(Exception):
    """وقتی پاسخ API به‌جای base64، یک URL برمی‌گرداند."""

    def __init__(self, url: str):
        super().__init__(url)
        self.url = url


async def generate_image(prompt: str) -> bytes:
    """
    با پرامپت داده‌شده یک تصویر تولید کرده و بایت‌های PNG/JPEG آن را برمی‌گرداند.
    خطاهای موقت (timeout/429/5xx) تا IMAGE_MAX_RETRIES بار با backoff نمایی
    تلاش مجدد می‌شوند.
    """
    path, payload = _build_request(prompt)
    client = _get_client()
    last_exc: Exception | None = None

    async with _semaphore:
        for attempt in range(1, settings.image_max_retries + 1):
            try:
                response = await client.post(path, json=payload)

                if response.status_code in _RETRYABLE_STATUS_CODES:
                    raise httpx.HTTPStatusError(
                        f"وضعیت قابل تلاش‌مجدد: {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()
                data = response.json()

                try:
                    b64 = _extract_image_b64(data)
                    return base64.b64decode(b64)
                except _NeedsUrlDownload as needs_url:
                    img_response = await client.get(needs_url.url)
                    img_response.raise_for_status()
                    return img_response.content

            except httpx.HTTPStatusError as exc:
                if (
                    exc.response is not None
                    and exc.response.status_code not in _RETRYABLE_STATUS_CODES
                ):
                    raise RuntimeError(
                        "درخواست به Image API با خطای غیرقابل‌تلاش‌مجدد رد شد "
                        f"({exc.response.status_code}): {exc.response.text[:300]}"
                    ) from exc

                last_exc = exc
                if attempt == settings.image_max_retries:
                    break
                wait = settings.image_retry_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "درخواست به Image API ناموفق بود (تلاش %s/%s): %s. تلاش مجدد بعد از %.1f ثانیه...",
                    attempt,
                    settings.image_max_retries,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                if attempt == settings.image_max_retries:
                    break
                wait = settings.image_retry_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "درخواست به Image API ناموفق بود (تلاش %s/%s): %s. تلاش مجدد بعد از %.1f ثانیه...",
                    attempt,
                    settings.image_max_retries,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)

    raise RuntimeError(
        f"درخواست به Image API پس از {settings.image_max_retries} تلاش ناموفق بود: {last_exc}"
    ) from last_exc
