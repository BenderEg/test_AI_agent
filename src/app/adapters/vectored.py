import asyncio
from collections.abc import AsyncGenerator, Callable
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from src.app.configs.settings import settings
from src.app.utils.utils import chunk_python_file_content


class BaseVectorAdapter:
    async def on_start_up(self) -> None: ...

    async def on_shut_down(self) -> None: ...

    async def upsert_content(self, content_gen: AsyncGenerator, repo_id: str) -> None:
        raise NotImplementedError

    async def search(
        self, query: str, repo_id: str | None, limit: int = 5, score_threshold: float | None = None
    ) -> list[dict]:
        raise NotImplementedError


class QdrantAdapter(BaseVectorAdapter):
    def __init__(self, embeder: Callable):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.embeder = embeder

    def create_collection(self, collection_name: str) -> None:
        collections_resp = self.client.get_collections()
        names = set(c.name for c in collections_resp.collections)
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

    async def search(
        self, query: str, repo_id: str | None, limit: int = 5, score_threshold: float | None = None
    ) -> list[dict]:
        query_filter = None
        if repo_id:
            query_filter = Filter(
                must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))]
            )
        results = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=self.embeder(query),
            limit=limit,
            query_filter=query_filter,
            score_threshold=score_threshold,
        )

        return [
            {
                "file": point.payload["file_path"],
                "symbol": point.payload["symbol"],
                "code": point.payload["text"],
            }
            for point in results.points
            if point.payload is not None
        ]

    async def upsert_content(self, content_gen: AsyncGenerator, repo_id: str) -> None:
        points = []
        async for file_path, content in content_gen:
            if not file_path or not content:
                continue
            chunks = chunk_python_file_content(content)
            for chunk in chunks:
                points.append(
                    PointStruct(
                        id=str(uuid4()),
                        vector=self.embeder(chunk["text"]),
                        payload={
                            "repo_id": repo_id,
                            "file_path": file_path,
                            "symbol": chunk["symbol"],
                            "type": chunk["type"],
                            "text": chunk["text"],
                        },
                    )
                )
        await asyncio.to_thread(
            self.client.upsert,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=points,
        )
