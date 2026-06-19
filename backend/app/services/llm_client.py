import asyncio
import logging
import re

import httpx

from app.config import settings

# برخی مدل‌های reasoning (مثل DeepSeek-R1) قبل از پاسخ نهایی یک بلوک
# <think>...</think> برمی‌گردانند که باید از خروجی نهایی حذف شود.
_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

logger = logging.getLogger("llm_client")

# یک Semaphore سراسری برای محدود کردن تعداد درخواست‌های هم‌زمان به API
# (مهم برای جلوگیری از rate-limit شدن یا overload شدن سرور مدل)
_semaphore = asyncio.Semaphore(settings.llm_max_concurrency)

# یک httpx.AsyncClient مشترک با connection pooling برای کارایی بهتر
# (به‌جای ساختن client جدید در هر request)
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.llm_base_url,
            timeout=settings.request_timeout,
            headers={
                "Authorization": f"apikey {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            limits=httpx.Limits(
                max_connections=settings.llm_max_concurrency * 2,
                max_keepalive_connections=settings.llm_max_concurrency,
            ),
        )
    return _client


async def aclose_client() -> None:
    """برای بستن تمیز connection pool هنگام shutdown سرویس."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


# خطاهایی که می‌توان برای آن‌ها retry کرد (مشکلات موقتی شبکه/سرور)
_RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


async def generate(prompt: str, system: str | None = None, model: str | None = None) -> str:
    """
    یک درخواست chat completion (فرمت OpenAI-Compatible) به API مدل می‌فرستد
    و متن پاسخ را برمی‌گرداند.

    - تعداد درخواست‌های هم‌زمان با Semaphore محدود می‌شود (LLM_MAX_CONCURRENCY).
    - در صورت خطای موقت (timeout / 429 / 5xx) با backoff نمایی تا
      LLM_MAX_RETRIES بار تلاش مجدد می‌شود.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or settings.llm_model,
        "messages": messages,
        "max_tokens": settings.llm_max_tokens,
        "temperature": settings.llm_temperature,
    }

    client = _get_client()
    last_exc: Exception | None = None

    async with _semaphore:
        for attempt in range(1, settings.llm_max_retries + 1):
            try:
                response = await client.post("/chat/completions", json=payload)

                if response.status_code in _RETRYABLE_STATUS_CODES:
                    raise httpx.HTTPStatusError(
                        f"وضعیت قابل تلاش‌مجدد: {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                # خطاهای دیگر (مثل 401 نامعتبر بودن apikey، 400 درخواست بد، 404)
                # قابل تلاش‌مجدد نیستند و باید فوراً بالا برده شوند.
                response.raise_for_status()
                data = response.json()
                return _extract_content(data)

            except httpx.HTTPStatusError as exc:
                if exc.response is not None and exc.response.status_code not in _RETRYABLE_STATUS_CODES:
                    # خطای قطعی (auth، bad request و...)؛ تلاش مجدد فایده‌ای ندارد.
                    raise RuntimeError(
                        f"درخواست به LLM API با خطای غیرقابل‌تلاش‌مجدد رد شد "
                        f"({exc.response.status_code}): {exc.response.text[:300]}"
                    ) from exc

                last_exc = exc
                if attempt == settings.llm_max_retries:
                    break
                wait = settings.llm_retry_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "درخواست به LLM API ناموفق بود (تلاش %s/%s): %s. تلاش مجدد بعد از %.1f ثانیه...",
                    attempt,
                    settings.llm_max_retries,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                if attempt == settings.llm_max_retries:
                    break
                wait = settings.llm_retry_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "درخواست به LLM API ناموفق بود (تلاش %s/%s): %s. تلاش مجدد بعد از %.1f ثانیه...",
                    attempt,
                    settings.llm_max_retries,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)

    raise RuntimeError(
        f"درخواست به LLM API پس از {settings.llm_max_retries} تلاش ناموفق بود: {last_exc}"
    ) from last_exc


def _extract_content(data: dict) -> str:
    """متن پاسخ را از ساختار استاندارد OpenAI chat completion استخراج می‌کند."""
    try:
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("پاسخ API هیچ choice ای نداشت.")
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        content = _THINK_BLOCK_RE.sub("", content)
        return content.strip()
    except (KeyError, IndexError, ValueError, AttributeError) as exc:
        raise RuntimeError(f"ساختار پاسخ API غیرمنتظره بود: {data}") from exc
