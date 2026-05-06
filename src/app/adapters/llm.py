import logging

from aiohttp import ClientError, ClientSession, ClientTimeout
from src.app.configs.settings import settings
from src.app.exceptions import LLMError

logger = logging.getLogger(__name__)


class BaseLLMAdapter:
    def __init__(self, session: ClientSession):
        self.session = session

    async def generate_response(self, prompt: str) -> str:
        raise NotImplementedError


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
