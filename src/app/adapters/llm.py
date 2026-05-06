import json
import logging
from collections.abc import AsyncGenerator

from aiohttp import ClientError, ClientSession, ClientTimeout
from src.app.configs.settings import settings
from src.app.exceptions import LLMError

logger = logging.getLogger(__name__)


class BaseLLMAdapter:
    def __init__(self, session: ClientSession):
        self.session = session

    async def generate_response(self, prompt: str) -> str:
        raise NotImplementedError

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        raise NotImplementedError
        yield  # makes this an async generator in the base class


class OllamaAdapter(BaseLLMAdapter):
    def __init__(self, session: ClientSession, model: str = settings.LLM_MODEL):
        self.model = model
        super().__init__(session)

    async def generate_response(self, prompt: str) -> str:
        try:
            async with self.session.post(
                url=f"{settings.llm_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=ClientTimeout(total=150),
            ) as resp:
                body = await resp.json()
        except ClientError as err:
            raise LLMError(f"Ollama request failed: {err}") from err
        if "response" not in body:
            raise LLMError(f"Unexpected Ollama response: {body}")
        return body["response"]

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            async with self.session.post(
                url=f"{settings.llm_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": True},
                timeout=ClientTimeout(total=150),
            ) as resp:
                async for raw_line in resp.content:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        body = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = body.get("response", "")
                    if token:
                        yield token
                    if body.get("done"):
                        break
        except ClientError as err:
            raise LLMError(f"Ollama streaming request failed: {err}") from err
