"""Qdrant collection lifecycle, upsert, delete, and search."""
import logging
import uuid
from datetime import datetime, timezone

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from config import (
    EMBEDDING_VECTOR_SIZE,
    KB_COLLECTION_NAME,
    KB_EMBED_BATCH_SIZE,
    QDRANT_API_KEY,
    QDRANT_PATH,
    QDRANT_URL,
)

_client: AsyncQdrantClient | None = None


def get_qdrant() -> AsyncQdrantClient:
    global _client
    if _client is None:
        if QDRANT_URL.strip():
            kwargs: dict = {"url": QDRANT_URL.strip(), "check_compatibility": False}
        else:
            kwargs: dict = {"path": QDRANT_PATH}
        if QDRANT_API_KEY:
            kwargs["api_key"] = QDRANT_API_KEY
        _client = AsyncQdrantClient(**kwargs)
    return _client


async def ensure_collection() -> None:
    client = get_qdrant()
    name = KB_COLLECTION_NAME
    try:
        await client.get_collection(name)
        return
    except Exception:
        pass

    await client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=EMBEDDING_VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )
    try:
        await client.create_payload_index(
            collection_name=name,
            field_name="document_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception:
        logging.exception("Payload index for document_id may already exist")


async def delete_by_document_id(document_id: str) -> None:
    client = get_qdrant()
    await client.delete(
        collection_name=KB_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )
        ),
    )


async def upsert_chunks(
    document_id: str,
    filename: str,
    chunks: list[str],
    vectors: list[list[float]],
    uploaded_at_iso: str,
) -> None:
    if len(chunks) != len(vectors):
        raise ValueError("chunks and vectors length mismatch")
    await ensure_collection()
    client = get_qdrant()
    points: list[PointStruct] = []
    for i, (text, vec) in enumerate(zip(chunks, vectors, strict=True)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": text[:12000],
                    "filename": filename[:512],
                    "uploaded_at": uploaded_at_iso,
                },
            )
        )
    await client.upsert(collection_name=KB_COLLECTION_NAME, points=points)


def _payload_as_dict(p: object) -> dict:
    if p is None:
        return {}
    if isinstance(p, dict):
        return p
    if hasattr(p, "model_dump"):
        return p.model_dump()  # type: ignore[no-any-return]
    return dict(p)  # type: ignore[arg-type]


async def search_chunks(
    query_vector: list[float],
    *,
    limit: int = 5,
    score_threshold: float | None = 0.25,
) -> list[dict]:
    await ensure_collection()
    client = get_qdrant()
    # qdrant-client >= 1.7: AsyncQdrantClient uses query_points, not search()
    resp = await client.query_points(
        collection_name=KB_COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True,
    )
    hits = resp.points or []
    out: list[dict] = []
    for h in hits:
        p = _payload_as_dict(getattr(h, "payload", None))
        out.append(
            {
                "score": float(h.score),
                "text": str(p.get("text", "")),
                "filename": str(p.get("filename", "")),
                "chunk_index": int(p.get("chunk_index", 0)),
                "document_id": str(p.get("document_id", "")),
            }
        )
    return out


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
