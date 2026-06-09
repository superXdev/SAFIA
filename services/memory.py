"""Long-term user memory backed by Qdrant — store facts, preferences, habits."""
import logging
import uuid
from datetime import datetime, timezone

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
    MEMORY_COLLECTION_NAME,
    MEMORY_SCORE_THRESHOLD,
    MEMORY_SEARCH_LIMIT,
)
from services.knowledge.embeddings import embed_query
from services.knowledge.qdrant_kb import get_qdrant

logger = logging.getLogger(__name__)


async def ensure_memory_collection() -> None:
    client = get_qdrant()
    name = MEMORY_COLLECTION_NAME
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
            field_name="user_id",
            field_schema=PayloadSchemaType.INTEGER,
        )
    except Exception:
        logger.debug("Payload index for user_id may already exist")


async def store_memory(user_id: int, fact: str, category: str = "general") -> str:
    """Embed and store a fact about a user. Returns the point ID."""
    await ensure_memory_collection()
    client = get_qdrant()
    vector = await embed_query(fact)
    point_id = str(uuid.uuid4())

    await client.upsert(
        collection_name=MEMORY_COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "user_id": user_id,
                    "fact": fact,
                    "category": category,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        ],
    )
    return point_id


async def search_memories(
    user_id: int, query: str, limit: int = MEMORY_SEARCH_LIMIT
) -> list[dict]:
    """Semantic search memories for a user. Returns [{fact, category, score, id}]."""
    await ensure_memory_collection()
    client = get_qdrant()
    vector = await embed_query(query)

    resp = await client.query_points(
        collection_name=MEMORY_COLLECTION_NAME,
        query=vector,
        query_filter=Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            ]
        ),
        limit=limit,
        score_threshold=MEMORY_SCORE_THRESHOLD,
        with_payload=True,
    )
    hits = resp.points or []
    out: list[dict] = []
    for h in hits:
        p = h.payload
        if not p:
            continue
        out.append(
            {
                "id": str(h.id),
                "fact": str(p.get("fact", "")),
                "category": str(p.get("category", "general")),
                "score": float(h.score),
            }
        )
    return out


async def list_memories(user_id: int) -> list[dict]:
    """List all memories for a user (scroll). Returns [{fact, category, id}]."""
    await ensure_memory_collection()
    client = get_qdrant()

    resp = await client.scroll(
        collection_name=MEMORY_COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            ]
        ),
        with_payload=True,
        limit=100,
    )
    points = resp[0] or []
    out: list[dict] = []
    for p in points:
        payload = p.payload
        if not payload:
            continue
        out.append(
            {
                "id": str(p.id),
                "fact": str(payload.get("fact", "")),
                "category": str(payload.get("category", "general")),
            }
        )
    return out


async def delete_memory(point_id: str) -> bool:
    """Delete a specific memory by point ID."""
    try:
        client = get_qdrant()
        await client.delete(
            collection_name=MEMORY_COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[]  # delete by point IDs passed separately
                )
            ),
            points=[point_id],
        )
        return True
    except Exception:
        logger.exception("Failed to delete memory %s", point_id)
        return False


async def clear_memories(user_id: int) -> int:
    """Delete all memories for a user. Returns number of points deleted."""
    client = get_qdrant()
    await client.delete(
        collection_name=MEMORY_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(key="user_id", match=MatchValue(value=user_id))
                ]
            )
        ),
    )
    return 0  # qdrant doesn't return count from delete
