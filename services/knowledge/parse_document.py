"""Extract plain text from PDF, DOCX, or plain text bytes."""
import logging
from io import BytesIO


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    try:
        if name.endswith(".pdf"):
            return _pdf_text(data)
        if name.endswith(".docx"):
            return _docx_text(data)
        return data.decode("utf-8", errors="replace")
    except Exception:
        logging.exception("Document parse failed for %s", filename)
        return ""


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        t = t.strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts)


def _docx_text(data: bytes) -> str:
    from docx import Document

    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text and p.text.strip())
