from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.app.utils.logger import get_logger
from src.app.configs.di import github_parser, llm_adapter, vector_adapter
from src.app.schemas.repo import AskQueryInfo, IngestRepo, QueryInfo, QueryResponseItem
from src.app.use_cases.base import ask, ingest, query

logger = get_logger(__name__)


router = APIRouter(
    prefix="/repo_parser",
    tags=["Парсер Github репозиториев для создания контекста"],
)


@router.get(
    "/ask",
    status_code=HTTPStatus.OK,
    description="Отправка запроса к LLM",
    summary="Отправка запроса к LLM",
)
async def ask_llm(
    llm_adapter: llm_adapter,
    vector_adapter: vector_adapter,
    data: AskQueryInfo = Query(),
) -> dict:
    answer = await ask(data, vector_adapter, llm_adapter)
    return {"answer": answer}


@router.get(
    "/query",
    status_code=HTTPStatus.OK,
    description="Отправка запроса к базе знаний",
    summary="Отправка запроса к базе знаний",
    response_model=list[QueryResponseItem],
)
async def query_info(
    vector_adapter: vector_adapter,
    data: QueryInfo = Query(),
) -> list[QueryResponseItem]:
    return await query(data, vector_adapter)


@router.post(
    "/ingest",
    status_code=HTTPStatus.OK,
    description="Отправка запроса для парсинга репозитория",
    summary="Отправка запроса для парсинга репозитория",
)
async def ingest_repo(
    data: IngestRepo,
    github_parser: github_parser,
    vector_adapter: vector_adapter,
) -> None:
    try:
        await ingest(data, github_parser, vector_adapter)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )