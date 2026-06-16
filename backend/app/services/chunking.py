SENTENCE_BREAKERS = ["\n\n", "\n", "۔", "؟", "!", ". "]


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    متن را به chunk هایی با حداکثر `chunk_size` کاراکتر تقسیم می‌کند.
    تلاش می‌کند مرز chunk ها را روی پایان پاراگراف/جمله قرار دهد تا
    جمله‌ها وسط بریده نشوند. بین chunk های پیاپی، `overlap` کاراکتر
    هم‌پوشانی وجود دارد تا context بین آن‌ها حفظ شود.
    """
    text = text.strip()
    if not text:
        return []

    if chunk_size <= overlap:
        raise ValueError("chunk_size باید بزرگ‌تر از overlap باشد")

    chunks: list[str] = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + chunk_size, n)

        if end < n:
            best_break = -1
            for sep in SENTENCE_BREAKERS:
                idx = text.rfind(sep, start, end)
                if idx != -1 and idx > start + chunk_size // 2:
                    candidate = idx + len(sep)
                    if candidate > best_break:
                        best_break = candidate
            if best_break != -1:
                end = best_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break

        start = max(end - overlap, start + 1)

    return chunks
