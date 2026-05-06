import asyncio
import logging

from src.app.adapters.github_parser import GitHubParser
from src.app.adapters.llm import BaseLLMAdapter
from src.app.adapters.vectored import BaseVectorAdapter
from src.app.configs.settings import settings
from src.app.schemas.repo import AskQueryInfo, IngestRepo, QueryInfo, QueryResponseItem
from src.app.use_cases.prompts import build_context, build_prompt, rewrite_prompt
from src.app.utils.utils import gen_repo_id

logger = logging.getLogger(__name__)


async def ingest(
    data: IngestRepo,
    parser: GitHubParser,
    vector_adapter: BaseVectorAdapter,
) -> None:
    repo_id = gen_repo_id(owner=data.owner, repo=data.repo, branch=data.branch)
    logger.info("ingest_start owner=%s repo=%s branch=%s force=%s", data.owner, data.repo, data.branch, data.force)
    if data.force:
        await vector_adapter.delete_by_repo_id(repo_id)
    content_generator = parser.get_repo_content(
        owner=data.owner,
        repo=data.repo,
        branch=data.branch,
    )
    await vector_adapter.upsert_content(content_gen=content_generator, repo_id=repo_id)
    logger.info("ingest_complete owner=%s repo=%s", data.owner, data.repo)


async def query(data: QueryInfo, vector_adapter: BaseVectorAdapter) -> list[QueryResponseItem]:
    repo_id = None
    if data.repo and data.owner and data.branch:
        repo_id = gen_repo_id(owner=data.owner, repo=data.repo, branch=data.branch)
    logger.info("query query=%r limit=%s threshold=%s", data.query, data.limit, data.score_threshold)
    results = await vector_adapter.search(data.query, repo_id, data.limit or 5, data.score_threshold)
    return [QueryResponseItem(**r) for r in results]


async def ask(
    data: AskQueryInfo, vector_adapter: BaseVectorAdapter, llm_adapter: BaseLLMAdapter
) -> str:
    logger.info("ask adapt_query=%s query=%r", data.adapt_user_query, data.query)
    if data.adapt_user_query:
        prompt = rewrite_prompt(data.query)
        data.query = await llm_adapter.generate_response(prompt)

    # Fetch a larger candidate set so the reranker has more to work with
    fetch_limit = (data.limit or 5) * 3 if settings.RERANKER_ENABLED else (data.limit or 5)
    results = await vector_adapter.search(
        data.query, _repo_id(data), fetch_limit, data.score_threshold
    )

    if settings.RERANKER_ENABLED and results:
        from src.app.utils.reranker import rerank
        results = await asyncio.to_thread(rerank, data.query, results, data.limit or 5)

    items = [QueryResponseItem(**r) for r in results]
    context, truncated = build_context([r.model_dump() for r in items])
    if truncated:
        logger.warning("ask context_truncated query=%r", data.query)
    prompt = build_prompt(query=data.query, context=context, truncated=truncated)
    return await llm_adapter.generate_response(prompt)


def _repo_id(data: QueryInfo) -> str | None:
    if data.repo and data.owner and data.branch:
        return gen_repo_id(owner=data.owner, repo=data.repo, branch=data.branch)
    return None
