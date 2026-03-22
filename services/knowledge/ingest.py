"""Orchestrate ingest and delete for knowledge documents."""
import logging
import re
import uuid
from pathlib import Path

from config import KB_CHUNK_OVERLAP_WORDS, KB_CHUNK_WORDS, KB_UPLOAD_DIR
from services.database import kb_create_document
from services.knowledge.chunking import chunk_text
from services.knowledge.embeddings import embed_texts
from services.knowledge.parse_document import extract_text
from services.knowledge.qdrant_kb import delete_by_document_id, upsert_chunks, utc_now_iso


def _stored_file_path(document_id: str, filename: str) -> Path:
    base = Path(KB_UPLOAD_DIR)
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(filename).name)[:200]
    return base / f"{document_id}__{safe}"


async def ingest_bytes(
    *,
    filename: str,
    mime_type: str,
    data: bytes,
    title: str = "",
) -> tuple[bool, str]:
    """
    Parse, chunk, embed, upsert to Qdrant, save file copy, insert metadata row.
    Returns (ok, message_for_admin).
    """
    document_id = str(uuid.uuid4())
    text = extract_text(filename, data)
    if not text.strip():
        return False, "Tidak ada teks yang bisa diekstrak (cek format PDF/DOCX/TXT)."

    chunks = chunk_text(text, KB_CHUNK_WORDS, KB_CHUNK_OVERLAP_WORDS)
    if not chunks:
        return False, "Teks terlalu pendek setelah dibersihkan."

    try:
        vectors = await embed_texts(chunks)
    except Exception as e:
        logging.exception("Embedding failed during ingest")
        return False, f"Embedding gagal: {e}"

    if len(vectors) != len(chunks):
        return False, "Jumlah vektor embedding tidak cocok dengan jumlah chunk."

    uploaded_at = utc_now_iso()
    try:
        await upsert_chunks(document_id, filename, chunks, vectors, uploaded_at)
    except Exception as e:
        logging.exception("Qdrant upsert failed")
        return False, f"Gagal menyimpan ke Qdrant: {e}"

    try:
        path = _stored_file_path(document_id, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except Exception:
        logging.exception("Could not write KB file copy (vectors are stored)")

    display_title = (title or "").strip() or filename
    await kb_create_document(
        document_id,
        filename,
        mime_type,
        display_title,
        chunk_count=len(chunks),
        status="ready",
    )
    return True, f"Berhasil: {len(chunks)} chunk terindeks (document_id={document_id})."


async def delete_kb_document(document_id: str) -> None:
    try:
        await delete_by_document_id(document_id)
    except Exception:
        logging.exception("Qdrant delete failed for document_id=%s", document_id)
    # Remove any stored file with this document_id prefix
    base = Path(KB_UPLOAD_DIR)
    if base.is_dir():
        for p in base.glob(f"{document_id}__*"):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                logging.exception("Failed to delete KB file %s", p)
