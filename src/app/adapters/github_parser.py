import asyncio
import base64
from collections.abc import AsyncGenerator

import backoff
from aiohttp import ClientSession
from src.app.configs.settings import settings
from src.app.utils.utils import is_py_file


class GitHubParser:
    def __init__(
        self,
        session: ClientSession,
    ):
        self.session = session

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        }

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=(ValueError, asyncio.TimeoutError),
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
            content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            async with self.session.get(url=content_url, headers=self.headers) as resp:
                if resp.status > 404:
                    raise ValueError("Status code in worker greater than 404")
                body = await resp.json()
                if "content" in body:
                    content = base64.b64decode(body["content"]).decode("utf-8", errors="ignore")
                    return file_path, content
                else:
                    return file_path, None

    async def parse_repo_items(
        self,
        repo_items: list,
        owner: str,
        repo: str,
    ):
        python_files = filter(is_py_file, repo_items)
        semaphore = asyncio.Semaphore(value=20)
        tasks = [
            asyncio.create_task(
                self.worker(
                    sem=semaphore,
                    file_path=i["path"],
                    owner=owner,
                    repo=repo,
                )
            )
            for i in python_files
        ]
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                yield result
            except Exception:
                yield (None, None)

    async def get_repo_content(
        self,
        owner: str,
        repo: str,
        branch: str = "master",
    ) -> AsyncGenerator[tuple[str, dict], None]:
        async with self.session.get(
            url=f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
            headers=self.headers,
        ) as resp:
            if resp.status != 200:
                raise ValueError("Repo not found")
            body = await resp.json()
            repo_items = body.get("tree", [])
            async for file_path, content in self.parse_repo_items(
                repo_items=repo_items,
                owner=owner,
                repo=repo,
            ):
                yield file_path, content
