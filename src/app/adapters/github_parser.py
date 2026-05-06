import asyncio
import base64
import logging
from collections.abc import AsyncGenerator

import backoff
from aiohttp import ClientError, ClientSession
from src.app.configs.settings import settings
from src.app.utils.utils import is_py_file

logger = logging.getLogger(__name__)


class PermanentGitHubError(Exception):
    """Non-retryable GitHub API error (e.g. 401 Unauthorized, 403 Forbidden)."""


class GitHubParser:
    def __init__(self, session: ClientSession):
        self.session = session

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.GITHUB_TOKEN}"}

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=(ClientError, asyncio.TimeoutError),
        max_tries=5,
    )
    async def worker(
        self,
        sem: asyncio.Semaphore,
        file_path: str,
        owner: str,
        repo: str,
    ) -> tuple[str, str | None]:
        async with sem:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            async with self.session.get(url=url, headers=self.headers) as resp:
                if resp.status in (401, 403):
                    raise PermanentGitHubError(f"GitHub auth error status={resp.status}")
                if resp.status == 404:
                    return file_path, None
                if resp.status == 429 or resp.status >= 500:
                    raise ClientError(f"Retryable GitHub error status={resp.status}")
                body = await resp.json()
                if "content" in body:
                    content = base64.b64decode(body["content"]).decode("utf-8", errors="ignore")
                    logger.info("fetched file_path=%s", file_path)
                    return file_path, content
                return file_path, None

    async def parse_repo_items(
        self,
        repo_items: list,
        owner: str,
        repo: str,
    ) -> AsyncGenerator[tuple[str | None, str | None], None]:
        python_files = list(filter(is_py_file, repo_items))
        semaphore = asyncio.Semaphore(value=20)
        tasks = [
            asyncio.create_task(
                self.worker(sem=semaphore, file_path=item["path"], owner=owner, repo=repo)
            )
            for item in python_files
        ]
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                yield result
            except PermanentGitHubError:
                raise
            except Exception as err:
                logger.warning("worker_error error=%s", err)
                yield (None, None)

    async def get_repo_content(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
    ) -> AsyncGenerator[tuple[str | None, str | None], None]:
        async with self.session.get(
            url=f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
            headers=self.headers,
        ) as resp:
            if resp.status in (401, 403):
                raise PermanentGitHubError(f"GitHub auth error status={resp.status}")
            if resp.status != 200:
                raise ValueError(f"Repo not found or inaccessible: status={resp.status}")
            body = await resp.json()
            repo_items = body.get("tree", [])
        async for file_path, content in self.parse_repo_items(
            repo_items=repo_items, owner=owner, repo=repo
        ):
            yield file_path, content
