import asyncio
import hashlib
import logging
from collections.abc import AsyncGenerator, Callable

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)
from src.app.configs.settings import settings
from src.app.exceptions import VectorDBError
from src.app.utils.utils import chunk_python_file_content

logger = logging.getLogger(__name__)

UPSERT_BATCH_SIZE = 100


def _point_id(repo_id: str, file_path: str, symbol: str) -> str:
    """Deterministic ID so re-ingesting the same content is idempotent."""
    return hashlib.sha256(f"{repo_id}:{file_path}:{symbol}".encode()).hexdigest()[:32]


class BaseVectorAdapter:
    async def on_start_up(self) -> None: ...

    async def on_shut_down(self) -> None: ...

    async def upsert_content(self, content_gen: AsyncGenerator, repo_id: str) -> None:
        raise NotImplementedError

    async def delete_by_repo_id(self, repo_id: str) -> None:
        raise NotImplementedError

    async def search(
        self, query: str, repo_id: str | None, limit: int = 5, score_threshold: float | None = None
    ) -> list[dict]:
        raise NotImplementedError


class QdrantAdapter(BaseVectorAdapter):
    def __init__(self, embedder: Callable):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.embedder = embedder

    def create_collection(self, collection_name: str) -> None:
        collections_resp = self.client.get_collections()
        names = {c.name for c in collections_resp.collections}
        if collection_name not in names:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=384,
                    distance=Distance.COSINE,
                ),
            )

    async def on_start_up(self) -> None:
        await asyncio.to_thread(
            self.create_collection,
            collection_name=settings.QDRANT_COLLECTION_NAME,
        )

    async def delete_by_repo_id(self, repo_id: str) -> None:
        await asyncio.to_thread(
            self.client.delete,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))]
                )
            ),
        )
        logger.info("deleted existing points repo_id=%s", repo_id)

    async def search(
        self, query: str, repo_id: str | None, limit: int = 5, score_threshold: float | None = None
    ) -> list[dict]:
        query_filter = None
        if repo_id:
            query_filter = Filter(
                must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))]
            )
        try:
            results = await asyncio.to_thread(
                self.client.query_points,
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=self.embedder(query),
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold,
            )
        except Exception as err:
            raise VectorDBError(f"Qdrant query failed: {err}") from err

        hits = [
            {
                "file": point.payload["file_path"],
                "symbol": point.payload["symbol"],
                "code": point.payload["text"],
                "score": point.score,
            }
            for point in results.points
            if point.payload is not None
        ]
        logger.info("search result_count=%d limit=%d threshold=%s", len(hits), limit, score_threshold)
        return hits

    async def upsert_content(self, content_gen: AsyncGenerator, repo_id: str) -> None:
        """
        Streams content from the generator and upserts in batches of UPSERT_BATCH_SIZE.
        Point IDs are deterministic hashes of (repo_id, file_path, symbol) so
        re-ingesting the same repo replaces identical points without creating duplicates.
        """
        batch: list[PointStruct] = []
        total = 0

        async def _flush(b: list[PointStruct]) -> None:
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=b,
            )

        async for file_path, content in content_gen:
            if not file_path or not content:
                continue
            chunks = chunk_python_file_content(content, file_path)
            for chunk in chunks:
                batch.append(
                    PointStruct(
                        id=_point_id(repo_id, file_path, chunk["symbol"]),
                        vector=self.embedder(chunk["text"]),
                        payload={
                            "repo_id": repo_id,
                            "file_path": file_path,
                            "symbol": chunk["symbol"],
                            "type": chunk["type"],
                            "text": chunk["text"],
                        },
                    )
                )
                if len(batch) >= UPSERT_BATCH_SIZE:
                    await _flush(batch)
                    total += len(batch)
                    logger.info("upsert_batch batch=%d total=%d", len(batch), total)
                    batch = []

        if batch:
            await _flush(batch)
            total += len(batch)

        logger.info("upsert_complete total=%d repo_id=%s", total, repo_id)
