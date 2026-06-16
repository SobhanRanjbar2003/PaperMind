# Book Summarizer - Backend

بک‌اند خلاصه‌سازی کتاب با FastAPI + Ollama (مدل `gemma3:4b`).

## پیش‌نیازها

1. **Python 3.10+**
2. **Ollama** نصب و در حال اجرا (https://ollama.com)

```bash
ollama pull gemma3:4b
ollama serve   # معمولا به صورت سرویس خودکار اجرا می‌شود، روی http://localhost:11434
```

> توجه: مدلی به نام `gemma4:e4b` در Ollama وجود ندارد، احتمالا منظور `gemma3:4b` بوده است.
> اگر اسم دقیق مدل دیگری در نظر داری، فقط مقدار `OLLAMA_MODEL` در `.env` را عوض کن.

## نصب

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## اجرا

```bash
uvicorn app.main:app --reload --port 8000
```

سرور روی `http://localhost:8000` بالا می‌آید. مستندات تعاملی: `http://localhost:8000/docs`

## معماری خلاصه‌سازی (Map-Reduce)

1. **استخراج متن**: از روی PDF / DOCX / TXT
2. **Chunk بندی**: متن بر اساس `CHUNK_SIZE_CHARS` (پیش‌فرض ۶۰۰۰ کاراکتر) با هم‌پوشانی
   `CHUNK_OVERLAP_CHARS` تقسیم می‌شود (مرز chunk ها تا حد امکان روی پایان جمله/پاراگراف قرار می‌گیرد).
3. **Map**: هر chunk به صورت جدا توسط مدل خلاصه می‌شود.
4. **Reduce**: خلاصه‌ها به صورت گروهی (`MAX_GROUP_SIZE` تایی) به صورت تکراری
   با هم ادغام می‌شوند تا یک خلاصه‌ی واحد باقی بماند.
5. **Final**: خلاصه‌ی واحد نهایی، بازنویسی و ساختاردهی می‌شود تا حدود
   `TARGET_SUMMARY_WORDS` کلمه (پیش‌فرض ۴۵۰۰ کلمه ≈ ۱۰ صفحه) شود.

پردازش به صورت **job-based** و در background انجام می‌شود تا فرانت بتواند
وضعیت/پیشرفت را poll کند (کتاب‌های بزرگ ممکن است چند دقیقه طول بکشند).

## API

### 1) آپلود فایل و ساخت job

```
POST /api/jobs
Content-Type: multipart/form-data
Body: file=<book.pdf | book.docx | book.txt>
```

پاسخ:
```json
{
  "job_id": "uuid",
  "filename": "book.pdf",
  "char_count": 123456,
  "chunk_count": 21
}
```

### 2) شروع خلاصه‌سازی

```
POST /api/jobs/{job_id}/summarize
```

پاسخ: `{"job_id": "...", "status": "started"}`

### 3) چک کردن وضعیت/پیشرفت

```
GET /api/jobs/{job_id}
```

پاسخ:
```json
{
  "job_id": "...",
  "status": "summarizing | reducing | done | error | pending",
  "progress": 0.42,
  "message": null,
  "chunk_count": 21,
  "chunks_done": 9
}
```

فرانت باید این endpoint را هر ۱-۲ ثانیه poll کند تا `status == "done"` یا `"error"` شود.

### 4) گرفتن نتیجه نهایی

```
GET /api/jobs/{job_id}/result
```

پاسخ:
```json
{
  "job_id": "...",
  "summary": "متن خلاصه...",
  "word_count": 4480
}
```

## نکات برای production

- در حال حاضر job ها در یک دیکشنری in-memory نگه داشته می‌شوند (`JOBS` در
  `app/services/job_manager.py`). برای production و چند worker باید با
  Redis یا دیتابیس جایگزین شود.
- `CHUNK_SIZE_CHARS` را با توجه به context window مدل (`gemma3:4b` معمولا
  ۸۱۹۲ توکن) تنظیم کن. مقدار ۶۰۰۰ کاراکتر تقریبا معادل ۱۵۰۰-۲۰۰۰ توکن فارسی
  است و جای کافی برای prompt و خروجی باقی می‌گذارد.
- اگر کتاب بسیار حجیم باشد، می‌توان مرحله‌ی reduce را با موازی‌سازی
  (`asyncio.gather`) سریع‌تر کرد، اما باید با ظرفیت Ollama (یک مدل بارگذاری
  شده روی GPU/CPU) هماهنگ باشد.
