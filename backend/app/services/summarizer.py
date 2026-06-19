from app.config import settings
from app.services import llm_client

# مرحله Map: خلاصه کردن هر chunk به صورت جداگانه
MAP_SYSTEM_PROMPT = (
    "تو یک دستیار خلاصه‌سازی متون فارسی هستی. متن زیر بخشی از یک کتاب است. "
    "یک خلاصه‌ی دقیق، روان و بدون نظر شخصی از این بخش بنویس که نکات کلیدی، "
    "استدلال‌ها، شخصیت‌ها، رویدادها و اطلاعات مهم را حفظ کند. "
    "از تکرار، حاشیه‌روی و اضافه کردن اطلاعاتی که در متن نیست خودداری کن. "
    "فقط متن خلاصه را بنویس، بدون هیچ مقدمه یا توضیح اضافه."
)

# مرحله Reduce: ادغام چند خلاصه در یک خلاصه‌ی یکپارچه‌تر
REDUCE_SYSTEM_PROMPT = (
    "تو یک دستیار خلاصه‌سازی متون فارسی هستی. در ادامه چند خلاصه از بخش‌های "
    "مختلف یک کتاب آمده است. این خلاصه‌ها را در یک خلاصه‌ی یکپارچه، منسجم و "
    "روان ادغام کن. ترتیب زمانی یا منطقی مطالب را حفظ کن، مطالب تکراری را حذف "
    "کن و چیزی به محتوا اضافه نکن. فقط متن ادغام‌شده را بنویس."
)

# مرحله Final: تبدیل خلاصه‌ی نهایی به یک خروجی ساختارمند حدود N کلمه
FINAL_SYSTEM_PROMPT_TEMPLATE = (
    "تو یک ویراستار حرفه‌ای فارسی هستی. متن زیر خلاصه‌ی فعلی یک کتاب است. "
    "این متن را بازنویسی و ویرایش کن تا یک خلاصه‌ی کامل، خوانا و ساختارمند در "
    "حدود {target_words} کلمه (تقریبا ۱۰ صفحه) باشد. خلاصه را با تیتربندی "
    "منطقی (مثلا بر اساس فصل‌ها یا موضوعات اصلی کتاب) و پاراگراف‌بندی مناسب "
    "بنویس. به زبان فارسی روان و رسمی بنویس و چیزی به محتوای اصلی اضافه نکن. "
    "فقط متن خلاصه را بنویس."
)


async def summarize_chunk(chunk: str) -> str:
    prompt = f"متن:\n\n{chunk}\n\nخلاصه‌ی این بخش:"
    return await llm_client.generate(prompt, system=MAP_SYSTEM_PROMPT)


async def reduce_summaries(summaries: list[str]) -> str:
    combined = "\n\n---\n\n".join(summaries)
    prompt = f"خلاصه‌های زیر را در یک خلاصه‌ی یکپارچه ادغام کن:\n\n{combined}\n\nخلاصه‌ی یکپارچه:"
    return await llm_client.generate(prompt, system=REDUCE_SYSTEM_PROMPT)


async def finalize_summary(text: str) -> str:
    system = FINAL_SYSTEM_PROMPT_TEMPLATE.format(
        target_words=settings.target_summary_words
    )
    prompt = f"متن:\n\n{text}\n\nخلاصه‌ی نهایی:"
    return await llm_client.generate(prompt, system=system)
