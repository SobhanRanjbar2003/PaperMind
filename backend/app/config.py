from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── LLM Connection ────────────────────────────────────────────────────────
    llm_base_url: str = "url of llm model"
    llm_api_key: str = "api key model"
    llm_model: str = "your model is here"

    # Concurrency & retry
    llm_max_concurrency: int = 5
    llm_max_retries: int = 3
    llm_retry_backoff_seconds: float = 1.5
    request_timeout: int = 120

    # Generation defaults
    llm_temperature: float = 0.3
    llm_max_tokens: int = 3000

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    # ── Chunking ─────────────────────────────────────────────────────────────
    chunk_size_chars: int = 6000
    chunk_overlap_chars: int = 300

    # ── Summarization ────────────────────────────────────────────────────────
    target_summary_words: int = 4500
    max_group_size: int = 5

    # ── Presentation (PPTX) ──────────────────────────────────────────────────
    presentation_llm_model: str | None = None
    presentation_llm_max_tokens: int = 6000
    presentation_llm_temperature: float = 0.4
    presentation_min_slides: int = 8
    presentation_max_slides: int = 16
    presentation_font_fa: str = "B Nazanin"
    presentation_font_fa_fallback: str = "Tahoma"
    presentation_slide_width_in: float = 13.333
    presentation_slide_height_in: float = 7.5
    presentation_output_dir: str = "generated_presentations"

    # ── Mind Map ─────────────────────────────────────────────────────────────
    mindmap_llm_model: str | None = None
    mindmap_llm_max_tokens: int = 4000
    mindmap_llm_temperature: float = 0.3
    mindmap_max_depth: int = 5
    mindmap_max_children: int = 5
    mindmap_first_pass_depth: int = 3
    mindmap_branch_context_chars: int = 9000
    mindmap_expand_max_concurrency: int = 5

    # ── Q&A ──────────────────────────────────────────────────────────────────
    qa_llm_model: str | None = None
    qa_llm_max_tokens: int = 4000
    qa_llm_temperature: float = 0.4
    qa_default_count_multiple_choice: int = 10
    qa_default_count_descriptive: int = 5
    qa_default_count_fill_blank: int = 10
    qa_max_count: int = 20

    class Config:
        env_file = ".env"


settings = Settings()
