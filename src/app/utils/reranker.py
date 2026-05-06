import logging

from sentence_transformers import CrossEncoder
from src.app.configs.settings import settings

logger = logging.getLogger(__name__)

# Loaded lazily on first call; warmed up at startup in lifespan to avoid cold-start latency.
_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(settings.RERANKER_MODEL)
        logger.info("reranker_loaded model=%s", settings.RERANKER_MODEL)
    return _model


def rerank(query: str, results: list[dict], top_k: int) -> list[dict]:
    """
    Two-stage retrieval: bi-encoder (vector search) fetches candidates, this Cross-Encoder
    scores each (query, code) pair jointly for higher-precision ranking.
    Model: ms-marco-MiniLM-L-6-v2 — industry-standard MSMARCO passage reranking benchmark.
    """
    if not results:
        return results
    model = _get_model()
    pairs = [(query, r["code"]) for r in results]
    scores = model.predict(pairs)  # type: ignore[arg-type]
    ranked = sorted(zip(scores, results, strict=False), key=lambda x: x[0], reverse=True)
    top = ranked[:top_k]
    logger.info("rerank candidates=%d top_k=%d", len(results), top_k)
    return [{**r, "rerank_score": float(score)} for score, r in top]


def warmup() -> None:
    """Call at startup (inside asyncio.to_thread) to pre-load the model weights."""
    _get_model().predict([("warmup", "warmup")])
    logger.info("reranker_warmup complete")
