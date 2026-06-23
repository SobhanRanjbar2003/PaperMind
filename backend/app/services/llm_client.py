"""
Async LLM client with connection pooling, concurrency limits, and retry logic.
Compatible with any OpenAI-compatible API (ArvanCloud, Together, etc.).
"""

import asyncio
import logging
import re

import httpx

from app.config import settings

# Strip <think>...</think> blocks emitted by some reasoning models (e.g. DeepSeek-R1)
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(settings.llm_max_concurrency)
_client: httpx.AsyncClient | None = None

# HTTP status codes that are transient and safe to retry
_RETRYABLE = {408, 409, 425, 429, 500, 502, 503, 504}


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
    """Gracefully close the shared connection pool on shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def generate(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> str:
    """
    Send a chat-completion request and return the assistant text.

    Concurrency is bounded by `llm_max_concurrency`. Transient errors
    (timeout / 429 / 5xx) are retried with exponential backoff up to
    `llm_max_retries` attempts.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or settings.llm_model,
        "messages": messages,
        "max_tokens": max_tokens or settings.llm_max_tokens,
        "temperature": temperature if temperature is not None else settings.llm_temperature,
    }

    client = _get_client()
    last_exc: Exception | None = None

    async with _semaphore:
        for attempt in range(1, settings.llm_max_retries + 1):
            try:
                response = await client.post("/chat/completions", json=payload)

                if response.status_code in _RETRYABLE:
                    raise httpx.HTTPStatusError(
                        f"retryable status {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()
                return _parse_content(response.json())

            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code if exc.response is not None else None
                if code is not None and code not in _RETRYABLE:
                    raise RuntimeError(
                        f"LLM API non-retryable error ({code}): {exc.response.text[:300]}"
                    ) from exc
                last_exc = exc

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc

            if attempt == settings.llm_max_retries:
                break

            wait = settings.llm_retry_backoff_seconds * (2 ** (attempt - 1))
            logger.warning(
                "LLM request failed (attempt %s/%s): %s – retrying in %.1fs",
                attempt,
                settings.llm_max_retries,
                last_exc,
                wait,
            )
            await asyncio.sleep(wait)

    raise RuntimeError(
        f"LLM API failed after {settings.llm_max_retries} attempts: {last_exc}"
    ) from last_exc


def _parse_content(data: dict) -> str:
    """Extract and clean the assistant message text from an API response."""
    try:
        content = data["choices"][0]["message"]["content"] or ""
        return _THINK_RE.sub("", content).strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected API response structure: {data}") from exc
