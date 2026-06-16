import io

from docx import Document
from pypdf import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    """متن خام را از فایل آپلودشده بر اساس پسوند آن استخراج می‌کند."""
    name = filename.lower()

    if name.endswith(".pdf"):
        return _extract_pdf(content)
    if name.endswith(".docx"):
        return _extract_docx(content)
    if name.endswith(".txt") or name.endswith(".md"):
        return content.decode("utf-8", errors="ignore")

    raise ValueError(
        f"فرمت فایل پشتیبانی نمی‌شود: {filename}. فقط pdf, docx, txt, md مجاز است."
    )


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
    return "\n".join(pages_text)


def _extract_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)
