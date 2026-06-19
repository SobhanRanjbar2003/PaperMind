# ---- مرحله build: نصب وابستگی‌ها در یک virtualenv جدا ----
FROM python:3.12-slim AS builder

WORKDIR /app

# ابزارهای build فقط برای کامپایل پکیج‌های native لازم هستن (مثل pypdf/lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ---- مرحله نهایی: image سبک فقط با runtime ----
FROM python:3.12-slim

WORKDIR /app

# کاربر غیر-root برای امنیت بهتر
RUN groupadd -r appuser && useradd -r -g appuser appuser

# کپی virtualenv آماده از مرحله build (بدون ابزارهای build)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY app ./app

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# uvloop و httptools از طریق uvicorn[standard] فعال هستن => سرعت بیشتر I/O
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
