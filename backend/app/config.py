from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # آدرس و مدل Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"

    # تنظیمات chunk بندی متن (بر اساس کاراکتر)
    chunk_size_chars: int = 6000
    chunk_overlap_chars: int = 300

    # هدف خلاصه نهایی (تقریبا 10 صفحه ~ 450 کلمه در هر صفحه)
    target_summary_words: int = 4500

    # تعداد خلاصه‌هایی که در هر دور reduce با هم ادغام می‌شوند
    max_group_size: int = 5

    # timeout هر درخواست به مدل (ثانیه) - مدل‌های لوکال می‌توانند کند باشند
    request_timeout: int = 300

    class Config:
        env_file = ".env"


settings = Settings()
