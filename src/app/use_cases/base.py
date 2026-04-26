from src.app.adapters.llm import BaseLLMAdapter
from src.app.adapters.vectored import BaseVectorAdapter
from src.app.adapters.github_parser import GitHubParser
from src.app.schemas.repo import AskQueryInfo, IngestRepo, QueryInfo

from src.app.utils.utils import gen_repo_id
from src.app.use_cases.promts import build_context, build_prompt, rewrite_prompt


async def ingest(
    data: IngestRepo,
    parser: GitHubParser,
    vector_adapter: BaseVectorAdapter,
) -> None:
    content_generator = parser.get_repo_content(
        owner=data.owner,
        repo=data.repo,
        branch=data.branch,
    )
    await vector_adapter.upsert_content(
        content_gen=content_generator,
        repo_id=gen_repo_id(
            owner=data.owner,
            repo=data.repo,
            branch=data.branch,
        )
    )


async def query(data: QueryInfo, vector_adapter: BaseVectorAdapter) -> list:
    repo_id = None
    if data.repo:
        repo_id = gen_repo_id(
            owner=data.owner,
            repo=data.repo,
            branch=data.branch,
        )
    return await vector_adapter.search(data.query, repo_id, data.limit)


async def ask(data: AskQueryInfo, vector_adapter: BaseVectorAdapter, llm_adapter: BaseLLMAdapter) -> str:
    if data.adapt_user_query:
        promt = rewrite_prompt(data.query)
        data.query = await llm_adapter.generate_response(promt)
    query_search = await query(data, vector_adapter)
    context = build_context(query_search)
    promt = build_prompt(query=data.query, context=context)
    return await llm_adapter.generate_response(promt)
