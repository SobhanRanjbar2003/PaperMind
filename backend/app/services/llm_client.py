import httpx

from app.config import settings


async def generate(prompt: str, system: str | None = None, model: str | None = None) -> str:
    """
    یک درخواست generate به Ollama می‌فرستد و متن پاسخ را برمی‌گرداند.
    """
    payload = {
        "model": model or settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        # برای خلاصه سازی بهتره خروجی نسبتا قطعی و کمتر خلاقانه باشه
        "options": {
            "temperature": 0.3,
        },
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate", json=payload
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("response") or "").strip()
