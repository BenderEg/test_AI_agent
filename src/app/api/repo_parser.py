from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Query, status
from src.app.configs.di import github_parser, llm_adapter, vector_adapter
from src.app.schemas.repo import (
    AskQueryInfo,
    AskResponse,
    IngestRepo,
    QueryInfo,
    QueryResponse,
)
from src.app.use_cases.base import ask, ingest, query
from src.app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/repo_parser",
    tags=["GitHub Repo Parser"],
)


@router.get(
    "/ask",
    status_code=HTTPStatus.OK,
    description="Ask a natural-language question about an ingested repository",
    summary="Ask LLM about a repository",
    response_model=AskResponse,
)
async def ask_llm(
    llm_adapter: llm_adapter,
    vector_adapter: vector_adapter,
    data: AskQueryInfo = Query(),
) -> AskResponse:
    answer = await ask(data, vector_adapter, llm_adapter)
    return AskResponse(answer=answer)


@router.get(
    "/query",
    status_code=HTTPStatus.OK,
    description="Vector-search the ingested codebase and return matching code chunks",
    summary="Query the knowledge base",
    response_model=QueryResponse,
)
async def query_info(
    vector_adapter: vector_adapter,
    data: QueryInfo = Query(),
) -> QueryResponse:
    items = await query(data, vector_adapter)
    return QueryResponse(
        items=items,
        total=len(items),
        score_threshold_used=data.score_threshold,
    )


@router.post(
    "/ingest",
    status_code=HTTPStatus.ACCEPTED,
    description="Fetch and index all Python files from a GitHub repository",
    summary="Ingest a GitHub repository",
)
async def ingest_repo(
    data: IngestRepo,
    github_parser: github_parser,
    vector_adapter: vector_adapter,
) -> None:
    logger.info("ingest_request owner=%s repo=%s branch=%s", data.owner, data.repo, data.branch)
    try:
        await ingest(data, github_parser, vector_adapter)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
