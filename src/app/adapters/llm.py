from aiohttp import ClientSession, ClientTimeout
from src.app.configs.settings import settings


class BaseLLMAdapter:
    def __init__(
        self,
        session: ClientSession,
    ):
        self.session = session

    async def generate_response(self, prompt: str) -> str:
        raise NotImplementedError


class OllamaAdapter(BaseLLMAdapter):
    def __init__(self, session: ClientSession, model: str = settings.LLM_MODEL):
        self.model = model
        super().__init__(session)

    async def generate_response(self, prompt: str) -> str:
        async with self.session.post(
            url=f"{settings.llm_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=ClientTimeout(total=150),
        ) as resp:
            body = await resp.json()
            return body["response"]
