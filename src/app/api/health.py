import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.app.adapters.vectored import QdrantAdapter
from src.app.configs.di import vector_adapter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}


@router.get(
    "/readiness",
    description="Checks connectivity to dependent services (Qdrant)",
    summary="Readiness probe",
)
async def readiness(vector_adapter: vector_adapter) -> JSONResponse:
    try:
        adapter: QdrantAdapter = vector_adapter
        await asyncio.to_thread(adapter.client.get_collections)
        return JSONResponse(status_code=200, content={"qdrant": "ok", "status": "ready"})
    except Exception as err:
        logger.warning("readiness_check_failed error=%s", err)
        return JSONResponse(status_code=503, content={"qdrant": "unreachable", "status": "degraded"})
