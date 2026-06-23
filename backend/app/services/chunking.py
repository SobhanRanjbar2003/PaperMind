"""Text chunking with sentence-boundary awareness and overlap."""

# Ordered by preference: prefer paragraph breaks, then sentence ends
_SENTENCE_BREAKERS = ["\n\n", "\n", "۔", "؟", "!", ". "]


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split *text* into chunks of at most *chunk_size* characters.

    Breaks are placed at natural sentence/paragraph boundaries whenever
    possible (within the last half of the chunk window). Consecutive
    chunks overlap by *overlap* characters to preserve cross-boundary
    context.
    """
    text = text.strip()
    if not text:
        return []
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks: list[str] = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + chunk_size, n)

        if end < n:
            best = -1
            for sep in _SENTENCE_BREAKERS:
                idx = text.rfind(sep, start, end)
                if idx != -1 and idx > start + chunk_size // 2:
                    candidate = idx + len(sep)
                    if candidate > best:
                        best = candidate
            if best != -1:
                end = best

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break

        start = max(end - overlap, start + 1)

    return chunks
