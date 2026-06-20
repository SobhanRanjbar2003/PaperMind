from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- تنظیمات اتصال به API مدل (سرور آروان / هر سرویس OpenAI-Compatible) ---
    # آدرس Endpoint پایه. توجه: مسیر /chat/completions به صورت خودکار اضافه می‌شود.
    # مثال: https://your-endpoint.arvanai.ir/v1
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

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

    # =========================================================
    # --- تنظیمات ساخت پاورپوینت (PPTX) از روی خلاصه ---
    # =========================================================

    # مدلی که برای طراحی ساختار اسلایدها (تیتر/بولت/پرامپت عکس) استفاده می‌شود.
    # پیش‌فرض همان مدل خلاصه‌سازی (llm_model) است؛ در صورت نیاز می‌توان جدا کرد.
    presentation_llm_model: str | None = None
    presentation_llm_max_tokens: int = 6000
    presentation_llm_temperature: float = 0.4

    # حداقل و حداکثر تعداد اسلاید محتوایی (بدون احتساب اسلاید عنوان/پایان)
    presentation_min_slides: int = 8
    presentation_max_slides: int = 16

    # فونت فارسی برای متن اسلایدها. باید روی سیستمی که فایل را باز می‌کند نصب باشد.
    # گزینه‌های رایج: "B Nazanin"، "IRANSans"، "Tahoma" (سازگاری بالا).
    presentation_font_fa: str = "B Nazanin"
    presentation_font_fa_fallback: str = "Tahoma"

    # ابعاد اسلاید: 16:9 عریض، مناسب ارائه کلاسی
    presentation_slide_width_in: float = 13.333
    presentation_slide_height_in: float = 7.5

    # پوشه‌ای که فایل‌های pptx ساخته‌شده در آن ذخیره می‌شوند
    presentation_output_dir: str = "generated_presentations"

    # --- تنظیمات اتصال به API تولید تصویر (مدل تصویرساز روی سرور آروان) ---
    # آدرس Endpoint پایه‌ی سرویس تصویرسازی (می‌تواند با LLM_BASE_URL متفاوت باشد).
    image_base_url: str = ""
    image_api_key: str = ""
    image_model: str = ""

    # مسیر endpoint نسبت به image_base_url. رایج‌ترین قرارداد OpenAI-Compatible
    # برای تولید تصویر همین "/images/generations" است.
    image_endpoint_path: str = "/images/generations"

    # شیوه‌ی ساخت payload / پردازش پاسخ. بسته به اینکه سرور آروان دقیقاً چه
    # قراردادی برای این مدل پیاده‌سازی کرده، یکی از این سه مقدار را انتخاب کنید:
    #   "openai_images"          -> قرارداد استاندارد POST /images/generations
    #   "openai_chat_multimodal" -> از طریق /chat/completions با خروجی تصویر در پیام
    #   "gemini"                 -> قرارداد Gemini-style generateContent
    # اگر مطمئن نیستید، با "openai_images" شروع کنید و طبق مستندات آروان
    # تنظیم کنید (به README بخش «تولید تصویر» مراجعه شود).
    image_request_style: str = "openai_images"

    image_size: str = "1024x1024"
    image_max_concurrency: int = 3
    image_max_retries: int = 3
    image_retry_backoff_seconds: float = 2.0
    image_request_timeout: int = 180

    # اگر تولید عکس برای یک اسلاید با خطا مواجه شد، پایپلاین کلاً fail نشود
    # و آن اسلاید بدون عکس (با چیدمان جایگزین) ساخته شود.
    image_fail_open: bool = True

    # =========================================================
    # --- تنظیمات ساخت Mind Map از روی خلاصه + متن کتاب ---
    # =========================================================

    # مدلی که برای ساخت mind map استفاده می‌شود (خالی = همان llm_model، یعنی gemma3)
    mindmap_llm_model: str | None = None
    mindmap_llm_max_tokens: int = 4000
    mindmap_llm_temperature: float = 0.3

    # حداکثر عمق کل درخت (ریشه = عمق ۰). یعنی با مقدار ۵، پایین‌ترین برگ‌ها در عمق ۴ هستند.
    mindmap_max_depth: int = 5

    # حداکثر تعداد فرزند مجاز برای هر نود (انشعاب)
    mindmap_max_children: int = 5

    # عمقی که مرحله‌ی اول (روی خلاصه‌ی نهایی) باید تا آنجا بسازد.
    # عمق باقی‌مانده (mindmap_max_depth - این عدد) در مرحله‌ی دوم با کمک
    # متن خام chunk های مرتبط با هر شاخه‌ی اصلی تکمیل می‌شود.
    mindmap_first_pass_depth: int = 3

    # حداکثر تعداد کاراکتر از متن خام chunk های مرتبط که برای تعمیق هر شاخه
    # به مدل داده می‌شود (برای کنترل هزینه/توکن)
    mindmap_branch_context_chars: int = 9000

    # حداکثر تعداد درخواست موازی LLM برای مرحله‌ی تعمیق شاخه‌ها
    mindmap_expand_max_concurrency: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
