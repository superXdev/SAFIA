"""Local embedding via fastembed (ONNX runtime, no GPU needed)."""
import logging
import shutil
import warnings
from pathlib import Path

from config import EMBEDDING_CACHE_DIR, EMBEDDING_LOCAL_MODEL

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding

        logging.info("Loading local embedding model: %s ...", EMBEDDING_LOCAL_MODEL)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            try:
                _embedder = TextEmbedding(
                    model_name=EMBEDDING_LOCAL_MODEL,
                    cache_dir=EMBEDDING_CACHE_DIR,
                )
            except Exception:
                logging.exception(
                    "Failed to load embedding model, clearing cache dir %s and retrying once...",
                    EMBEDDING_CACHE_DIR,
                )
                cache_path = Path(EMBEDDING_CACHE_DIR)
                if cache_path.exists():
                    shutil.rmtree(cache_path)
                _embedder = TextEmbedding(
                    model_name=EMBEDDING_LOCAL_MODEL,
                    cache_dir=EMBEDDING_CACHE_DIR,
                )
        logging.info("Local embedding model loaded.")
    return _embedder


def embed_texts_local(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_embedder()
    vectors = list(model.embed(texts))
    return [list(v) for v in vectors]


def embed_query_local(text: str) -> list[float]:
    return embed_texts_local([text])[0]


def warmup_local_embedding() -> None:
    """Preload the model at startup (optional, blocks briefly)."""
    _get_embedder()
