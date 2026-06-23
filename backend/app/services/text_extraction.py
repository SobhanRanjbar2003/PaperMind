"""Extract plain text from uploaded book files (PDF, DOCX, TXT, MD)."""

import io

from docx import Document
from pypdf import PdfReader

_SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


def extract_text(filename: str, content: bytes) -> str:
    """Return raw text from *content* based on *filename*'s extension."""
    ext = _extension(filename)
    if ext == ".pdf":
        return _from_pdf(content)
    if ext == ".docx":
        return _from_docx(content)
    if ext in {".txt", ".md"}:
        return content.decode("utf-8", errors="ignore")
    raise ValueError(
        f"Unsupported file format: {filename!r}. Allowed: {', '.join(sorted(_SUPPORTED))}"
    )


def _extension(filename: str) -> str:
    lower = filename.lower()
    for ext in _SUPPORTED:
        if lower.endswith(ext):
            return ext
    return ""


def _from_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _from_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)
