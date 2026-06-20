# Book Summarizer Backend

بک‌اند خلاصه‌سازی کتاب با FastAPI، با اتصال به هر سرویس OpenAI-Compatible (از جمله سرور آروان).

## معماری

پردازش از الگوی **Map → Reduce → Finalize** پیروی می‌کند:

1. **Map**: متن کتاب به chunk هایی تقسیم شده و همزمان (حداکثر `LLM_MAX_CONCURRENCY` درخواست موازی) به API مدل فرستاده می‌شود.
2. **Reduce**: خلاصه‌های بدست‌آمده در گروه‌هایی ادغام می‌شوند؛ هر دور ادغام نیز موازی اجرا می‌شود.
3. **Finalize**: خلاصه‌ی نهایی ویرایش شده و ساختارمند می‌شود.

موازی‌سازی با `asyncio.Semaphore` کنترل می‌شود تا تعداد درخواست‌های هم‌زمان از حد مجاز سرور مدل تجاوز نکند.

## راه‌اندازی سریع با Docker

### ۱. کپی و پر کردن فایل تنظیمات

```bash
cp backend/.env.example backend/.env
```

فایل `backend/.env` را باز کنید و مقادیر زیر را وارد کنید:

```env
LLM_BASE_URL=https://your-arvan-endpoint.example.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gemma3-1b
```

> **نکته مهم درباره `LLM_BASE_URL`:**
> مسیر `/chat/completions` به صورت خودکار اضافه می‌شود.
> اگر آدرس کامل شما `https://api.example.ir/v1/chat/completions` است،
> مقدار `LLM_BASE_URL` را `https://api.example.ir/v1` قرار دهید.

### ۲. اجرا

```bash
docker compose up -d --build
```

### ۳. بررسی سلامت سرویس

```bash
curl http://localhost:8000/
# {"status":"ok","service":"book-summarizer-api"}
```

### ۴. توقف

```bash
docker compose down
```

---

## راه‌اندازی بدون Docker (توسعه محلی)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # ویندوز: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # فایل .env را ویرایش کنید
uvicorn app.main:app --reload
```

---

## متغیرهای محیطی

| متغیر | پیش‌فرض | توضیح |
|-------|---------|-------|
| `LLM_BASE_URL` | — | آدرس پایه Endpoint (بدون `/chat/completions`) |
| `LLM_API_KEY` | — | کلید API |
| `LLM_MODEL` | `gemma3-1b` | نام مدل |
| `LLM_MAX_CONCURRENCY` | `5` | حداکثر درخواست هم‌زمان به API |
| `LLM_MAX_RETRIES` | `3` | تعداد تلاش مجدد برای خطاهای موقت (timeout/5xx/429) |
| `LLM_RETRY_BACKOFF_SECONDS` | `1.5` | تأخیر پایه retry (نمایی: ۱.۵ / ۳ / ۶ ثانیه) |
| `REQUEST_TIMEOUT` | `120` | timeout هر درخواست (ثانیه) |
| `LLM_TEMPERATURE` | `0.3` | دمای خروجی مدل |
| `LLM_MAX_TOKENS` | `3000` | حداکثر توکن خروجی |
| `CHUNK_SIZE_CHARS` | `6000` | اندازه هر chunk (کاراکتر) |
| `CHUNK_OVERLAP_CHARS` | `300` | هم‌پوشانی بین chunk ها (کاراکتر) |
| `TARGET_SUMMARY_WORDS` | `4500` | هدف کلمات خلاصه نهایی (~۱۰ صفحه) |
| `MAX_GROUP_SIZE` | `5` | حداکثر تعداد خلاصه‌های ادغامی در هر دور Reduce |
| `PRESENTATION_LLM_MODEL` | (=`LLM_MODEL`) | مدل طراحی ساختار اسلاید (خالی = همان مدل خلاصه‌سازی) |
| `PRESENTATION_LLM_MAX_TOKENS` | `6000` | حداکثر توکن خروجی برای JSON طرح اسلاید |
| `PRESENTATION_MIN_SLIDES` / `PRESENTATION_MAX_SLIDES` | `8` / `16` | بازه‌ی تعداد اسلاید محتوایی |
| `PRESENTATION_FONT_FA` | `B Nazanin` | فونت فارسی استفاده‌شده در فایل pptx (باید روی سیستم بازکننده نصب باشد) |
| `PRESENTATION_OUTPUT_DIR` | `generated_presentations` | پوشه‌ی ذخیره فایل‌های pptx ساخته‌شده |
| `IMAGE_BASE_URL` / `IMAGE_API_KEY` | — | اتصال به سرویس تصویرساز (می‌تواند جدا از LLM باشد) |
| `IMAGE_MODEL` | `Gemini-3-1-Flash-Lite-Preview-ax1s0` | نام مدل تصویرساز روی سرور آروان |
| `IMAGE_REQUEST_STYLE` | `openai_images` | قرارداد API: `openai_images` \| `openai_chat_multimodal` \| `gemini` |
| `IMAGE_MAX_CONCURRENCY` | `3` | حداکثر درخواست هم‌زمان تولید تصویر |
| `IMAGE_FAIL_OPEN` | `true` | اگر تولید عکس یک اسلاید خطا داد، پایپلاین کلاً fail نشود |
| `MINDMAP_LLM_MODEL` | (=`LLM_MODEL`) | مدل ساخت Mind Map (خالی = همان مدل خلاصه‌سازی، gemma3) |
| `MINDMAP_LLM_MAX_TOKENS` | `4000` | حداکثر توکن خروجی برای هر درخواست JSON مربوط به mind map |
| `MINDMAP_MAX_DEPTH` | `5` | حداکثر عمق کل درخت (ریشه = عمق ۰) |
| `MINDMAP_MAX_CHILDREN` | `5` | حداکثر تعداد فرزند (انشعاب) هر نود |
| `MINDMAP_FIRST_PASS_DEPTH` | `3` | عمقی که مرحله‌ی اول (روی خلاصه) می‌سازد؛ باقی عمق در مرحله‌ی دوم از متن خام تکمیل می‌شود |
| `MINDMAP_BRANCH_CONTEXT_CHARS` | `9000` | حداکثر کاراکتر متن خام مرتبط که برای تعمیق هر شاخه به مدل داده می‌شود |
| `MINDMAP_EXPAND_MAX_CONCURRENCY` | `5` | حداکثر درخواست هم‌زمان LLM در مرحله‌ی تعمیق شاخه‌ها |

---

## API

### آپلود فایل و ساخت job

```
POST /api/jobs
Content-Type: multipart/form-data
Body: file=<pdf|docx|txt|md>
```

```json
{"job_id": "uuid", "filename": "book.pdf", "char_count": 120000, "chunk_count": 20}
```

### شروع خلاصه‌سازی

```
POST /api/jobs/{job_id}/summarize
```

### بررسی وضعیت

```
GET /api/jobs/{job_id}
```

```json
{"job_id": "...", "status": "summarizing", "progress": 0.45, "chunk_count": 20, "chunks_done": 9}
```

وضعیت‌های ممکن: `pending` → `summarizing` → `reducing` → `done` | `error`

### دریافت نتیجه

```
GET /api/jobs/{job_id}/result
```

```json
{"job_id": "...", "summary": "خلاصه‌ی کامل کتاب...", "word_count": 4312}
```

---

## ساخت پاورپوینت از روی خلاصه (ویژگی جدید)

بعد از اینکه job به وضعیت `done` رسید (یعنی `GET /api/jobs/{job_id}` خروجی `status: "done"` داد)، می‌توانید از روی همان خلاصه یک فایل **.pptx** کامل و قابل‌ارائه بسازید.

### معماری این بخش

1. **`slide_planner`** — خلاصه‌ی متن را با همان LLM (آروان) به یک JSON ساختاریافته تبدیل می‌کند: عنوان ارائه، یک پالت رنگی مناسب (از بین ۱۰ پالت از پیش طراحی‌شده)، و فهرست اسلایدها (هرکدام با تیتر، ۳ تا ۵ بولت کوتاه، نوع چیدمان، و در صورت نیاز یک پرامپت تصویر).
2. **`image_client`** — برای اسلایدهایی که نیاز به تصویر دارند (و برای زمینه‌ی اسلاید عنوان)، با مدل `IMAGE_MODEL` (پیش‌فرض `Gemini-3-1-Flash-Lite-Preview-ax1s0` روی سرور آروان) تصویر تولید می‌کند. درخواست‌ها موازی (با سقف `IMAGE_MAX_CONCURRENCY`) و با retry/backoff انجام می‌شوند.
3. **`pptx_builder`** — فایل نهایی pptx (نسبت ۱۶:۹) را با `python-pptx` می‌سازد: راست‌چین کامل برای متن فارسی (RTL واقعی، نه فقط ظاهری)، فونت `PRESENTATION_FONT_FA`، چیدمان‌های متنوع (تصویر+بولت، بولت تمام‌عرض، نقل‌قول)، یک motif بصری تکرارشونده (دایره‌های شماره‌دار)، و یک اسلاید عنوان + جمع‌بندی.
4. **`presentation_manager`** — این سه مرحله را به‌صورت یک پایپلاین background اجرا و وضعیت را trace می‌کند؛ اگر تولید عکس یک اسلاید خاص خطا بدهد (و `IMAGE_FAIL_OPEN=true` باشد)، آن اسلاید بدون عکس (با یک shape تزئینی جایگزین) ساخته می‌شود و کل فرایند متوقف نمی‌شود.

### اندپوینت‌ها

**شروع ساخت ارائه:**
```
POST /api/jobs/{job_id}/presentation
```
```json
{"job_id": "...", "status": "pending"}
```

**بررسی وضعیت:**
```
GET /api/jobs/{job_id}/presentation
```
```json
{
  "job_id": "...",
  "status": "generating_images",
  "progress": 0.55,
  "slide_count": 12,
  "images_total": 8,
  "images_done": 5,
  "download_url": null
}
```
وضعیت‌های ممکن: `pending` → `planning` → `generating_images` → `building` → `done` | `error`

**دانلود فایل نهایی** (وقتی `status` برابر `done` شد):
```
GET /api/jobs/{job_id}/presentation/download
```
پاسخ: فایل `.pptx` آماده دانلود.

### ⚠️ نکته‌ی مهم درباره‌ی API تولید تصویر

قرارداد دقیق API سرویس تصویرساز شما روی آروان (برای مدل `Gemini-3-1-Flash-Lite-Preview-ax1s0`) مستندِ از پیش‌شناخته‌ای برای این پروژه نبود. کد فعلی (`app/services/image_client.py`) بر اساس متداول‌ترین قرارداد رایج (`openai_images`: درخواست `POST {IMAGE_BASE_URL}/images/generations` و پاسخ `{"data":[{"b64_json": "..."}]}`) نوشته شده و parser پاسخ هم چند ساختار رایج دیگر (chat multimodal، Gemini-style `generateContent`) را امتحان می‌کند. **پیشنهاد می‌شود قبل از استفاده‌ی واقعی:**

1. یک درخواست نمونه با `curl` به endpoint واقعی آروان برای این مدل بزنید و ساختار دقیق request/response را ببینید.
2. اگر فرمت متفاوت بود، مقدار `IMAGE_REQUEST_STYLE` را در `.env` عوض کنید یا توابع `_build_request` و `_extract_image_b64` در `image_client.py` را با نمونه‌ی واقعی پاسخ تطبیق دهید (هر دو تابع کوچک و مجزا هستند).
3. اگر سرویس آروان alpha-channel/PNG شفاف برنمی‌گرداند مشکلی نیست؛ تصاویر به‌صورت کامل (cover-fit، بدون کشیدگی) در اسلاید جا می‌شوند.

### نکات دیگر

- ساخت یک ارائه‌ی کامل معمولاً چند درخواست LLM (۱ یا ۲ برای طرح اسلاید) + چند درخواست تصویرسازی موازی (به تعداد اسلایدهای دارای تصویر) طول می‌کشد؛ به همین دلیل کاملاً async/background پیاده شده تا job اصلی summarization را بلاک نکند.
- فایل‌های pptx در `PRESENTATION_OUTPUT_DIR` (پیش‌فرض `generated_presentations/` کنار کد) ذخیره می‌شوند. اگر می‌خواهید بین ری‌استارت‌های کانتینر باقی بمانند، این مسیر را در `docker-compose.yml` به‌صورت یک volume mount کنید.
- چون فونت فارسی (`PRESENTATION_FONT_FA`, پیش‌فرض «B Nazanin») باید روی سیستمی که فایل را *باز می‌کند* نصب باشد نه روی سرور، در صورت نبود آن فونت، PowerPoint/LibreOffice به‌صورت خودکار با نزدیک‌ترین فونت موجود (مثلاً Tahoma) جایگزین می‌کند — متن همچنان درست و راست‌چین نمایش داده می‌شود.

---

## ساخت Mind Map (نقشه‌ی ذهنی) از روی خلاصه + متن کتاب (ویژگی جدید)

بعد از اینکه job به وضعیت `done` رسید، می‌توانید یک **Mind Map** درختی شبیه قابلیت Mind Map در NotebookLM بسازید: یک گراف (در اصل درخت) که از یک موضوع کلی شروع می‌شود و هرچه عمیق‌تر می‌رود به نکات جزئی‌تر می‌رسد.

### معماری این بخش (طراحی‌شده برای کمترین هزینه‌ی ممکن از مدل)

برخلاف بخش پاورپوینت، اینجا **هیچ مدل تصویرساز جدیدی استفاده نمی‌شود** و همان مدل خلاصه‌سازی (`LLM_MODEL`، یعنی gemma3) برای کل کار به کار می‌رود. کل پایپلاین فقط در **دو مرحله** و با حداقل تعداد درخواست LLM اجرا می‌شود:

1. **مرحله ۱ — `mindmap_builder.build_first_pass` (دقیقاً ۱ درخواست LLM):**
   از روی همان خلاصه‌ی نهایی متن (که قبلاً ساخته شده، پس از مدل دوباره استفاده نمی‌شود)، یک درخت با عمق `MINDMAP_FIRST_PASS_DEPTH` (پیش‌فرض ۳: ریشه + شاخه‌های اصلی + یک سطح زیرشاخه) ساخته می‌شود. چون خلاصه از قبل پاکسازی و فشرده شده، این مرحله ساختار کلی منسجمی تضمین می‌کند.

2. **مرحله ۲ — `mindmap_builder.expand_branches` (حداکثر «تعداد شاخه‌ی اصلی» درخواست، موازی):**
   برای هر شاخه‌ی اصلی (فرزند مستقیم ریشه)، بخشی از **متن خام و اصلی کتاب** (همان `chunks` ای که در مرحله‌ی خلاصه‌سازی ساخته شده بودند؛ بدون فراخوانی مجدد مدل برای chunk کردن) که تخمین زده می‌شود به آن شاخه مربوط است انتخاب و به مدل داده می‌شود تا عمق باقی‌مانده تا `MINDMAP_MAX_DEPTH` (پیش‌فرض ۵) با جزئیات واقعی (نه حدسی) تکمیل شود. انتخاب «کدام بخش از chunk ها به کدام شاخه مربوط است» با یک تخمین ساده‌ی رایگان (تقسیم متناسب بر اساس ترتیب چاپ/خلاصه‌سازی کتاب) انجام می‌شود — **بدون درخواست اضافه به LLM برای matching**.

   نتیجه: برای کتابی با مثلاً ۵ شاخه‌ی اصلی، کل Mind Map با **۱ + ۵ = ۶ درخواست LLM** ساخته می‌شود؛ نه به تعداد کل chunk های کتاب. این درخواست‌ها هم به‌صورت موازی (با سقف `MINDMAP_EXPAND_MAX_CONCURRENCY`) اجرا می‌شوند تا سریع باشند.

3. **`mindmap_builder.assign_ids_and_flatten`** (بدون فراخوانی مدل): درخت نهایی را اعتبارسنجی، عمق آن را دقیقاً به `MINDMAP_MAX_DEPTH` محدود می‌کند (هر برگ عمیق‌تر حذف می‌شود)، به هر نود یک `id` یکتا می‌دهد و دو خروجی می‌سازد: یک نسخه‌ی **درختی تو در تو** (`tree`، مناسب رندرهای سلسله‌مراتبی مثل markmap) و یک نسخه‌ی **مسطح nodes/edges** (مناسب کتابخونه‌هایی مثل **React Flow**).

4. **`mindmap_manager`** این مراحل را به‌صورت یک پایپلاین background اجرا و وضعیت/پیشرفت را trace می‌کند (دقیقاً مثل الگوی `presentation_manager`).

### محدودیت‌های ساختاری درخت

- **حداکثر عمق کل درخت: ۵ سطح** (ریشه = عمق ۰؛ پایین‌ترین برگ‌ها در عمق ۴ هستند) — قابل تنظیم با `MINDMAP_MAX_DEPTH`.
- **حداکثر انشعاب هر نود: ۵ فرزند** (تعداد واقعی فرزندان هر نود می‌تواند کمتر باشد، بسته به موضوع، اما هرگز بیشتر) — قابل تنظیم با `MINDMAP_MAX_CHILDREN`.
- برچسب هر نود کوتاه نگه داشته می‌شود (چند کلمه‌ی کلیدی، نه جمله‌ی کامل) تا در فرانت داخل باکس‌های نمودار جا شود.

### اندپوینت‌ها

**شروع ساخت Mind Map:**
```
POST /api/jobs/{job_id}/mindmap
```
```json
{"job_id": "...", "status": "pending"}
```

**بررسی وضعیت:**
```
GET /api/jobs/{job_id}/mindmap
```
```json
{
  "job_id": "...",
  "status": "expanding",
  "progress": 0.55,
  "node_count": 0,
  "branch_count": 5,
  "branches_done": 2
}
```
وضعیت‌های ممکن: `pending` → `planning` → `expanding` → `done` | `error`

**دریافت نتیجه‌ی نهایی** (وقتی `status` برابر `done` شد):
```
GET /api/jobs/{job_id}/mindmap/result
```
```json
{
  "job_id": "...",
  "title": "موضوع کلی کتاب",
  "max_depth": 5,
  "node_count": 42,
  "tree": {
    "id": "a1b2c3d4",
    "label": "موضوع کلی کتاب",
    "depth": 0,
    "children": [
      {
        "id": "e5f6a7b8",
        "label": "شاخه‌ی اصلی ۱",
        "depth": 1,
        "children": [ { "...": "تا عمق ۴" } ]
      }
    ]
  },
  "nodes": [
    {"id": "a1b2c3d4", "label": "موضوع کلی کتاب", "depth": 0, "parent_id": null},
    {"id": "e5f6a7b8", "label": "شاخه‌ی اصلی ۱", "depth": 1, "parent_id": "a1b2c3d4"}
  ],
  "edges": [
    {"id": "e-a1b2c3d4-e5f6a7b8", "source": "a1b2c3d4", "target": "e5f6a7b8"}
  ]
}
```

### استفاده در فرانت

دو فیلد `tree` و `nodes`/`edges` همزمان برگردانده می‌شوند تا فرانت مجبور به تبدیل ساختار نباشد:

- **`tree`** (درخت تو در تو با `children`): مناسب برای رندر مستقیم با کتابخونه‌هایی مثل [`markmap`](https://markmap.js.org/) یا هر رندر سلسله‌مراتبی دیگر (D3 tree/cluster layout و مانند آن).
- **`nodes`** + **`edges`** (لیست مسطح با `parent_id` روی هر نود و یال‌های جدا): دقیقاً فرمتی که **React Flow** (`<ReactFlow nodes={...} edges={...} />`) انتظار دارد؛ کافی است `position` را خودتان با یک الگوریتم layout (مثلاً [`dagre`](https://github.com/dagrejs/dagre) یا `elkjs`) بر اساس `depth` و `parent_id` محاسبه کنید، یا از `tree` برای layout دایره‌ای/شعاعی استفاده کنید.

هر نود همچنین فیلد `depth` دارد (۰ تا ۴) که می‌تواند مستقیماً برای رنگ‌بندی/اندازه‌ی متفاوت هر سطح در UI استفاده شود.



- **تعداد Worker**: به دلیل استفاده از حافظه in-memory برای ذخیره‌ی jobها، حتماً با **۱ worker** اجرا کنید. Dockerfile این را به صورت پیش‌فرض تنظیم کرده است.
- **مدل‌های Reasoning**: اگر مدل شما (مثل DeepSeek-R1) بلوک `<think>...</think>` برمی‌گرداند، کلاینت آن را به صورت خودکار از خروجی نهایی حذف می‌کند.
- **Retry هوشمند**: خطاهای موقت (timeout، ۴۲۹، ۵xx) تا `LLM_MAX_RETRIES` بار با backoff نمایی retry می‌شوند. خطاهای قطعی (۴۰۱، ۴۰۰) بلافاصله با پیام واضح fail می‌شوند.
