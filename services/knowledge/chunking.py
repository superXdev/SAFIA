"""Split plain text into overlapping windows (by words)."""


def chunk_text(text: str, chunk_words: int, overlap_words: int) -> list[str]:
    """Split on whitespace; each chunk is up to `chunk_words` tokens, sliding by `chunk_words - overlap_words`."""
    words = text.strip().split()
    if not words:
        return []
    if chunk_words <= 0:
        return [" ".join(words)]
    if overlap_words >= chunk_words:
        overlap_words = max(0, chunk_words // 4)

    chunks: list[str] = []
    n = len(words)
    start = 0
    while start < n:
        end = min(start + chunk_words, n)
        chunks.append(" ".join(words[start:end]))
        if end >= n:
            break
        start = end - overlap_words
    return chunks
