from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    llm_base_url: str = "https://api.example.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gemma3-1b"

    # درجه موازی‌سازی: حداکثر تعداد درخواست هم‌زمان به API (هم برای Map و هم Reduce)
    llm_max_concurrency: int = 5

    # تعداد تلاش مجدد در صورت خطای موقت (timeout/5xx/connection) + backoff پایه (ثانیه)
    llm_max_retries: int = 3
    llm_retry_backoff_seconds: float = 1.5

    # timeout هر درخواست به مدل (ثانیه)
    request_timeout: int = 120

    # temperature برای خلاصه‌سازی (مقدار پایین = خروجی قطعی‌تر)
    llm_temperature: float = 0.3
    llm_max_tokens: int = 3000

    # --- تنظیمات chunk بندی متن (بر اساس کاراکتر) ---
    chunk_size_chars: int = 6000
    chunk_overlap_chars: int = 300

    # هدف خلاصه نهایی (تقریبا 10 صفحه ~ 450 کلمه در هر صفحه)
    target_summary_words: int = 4500

    # تعداد خلاصه‌هایی که در هر دور reduce با هم ادغام می‌شوند
    max_group_size: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
