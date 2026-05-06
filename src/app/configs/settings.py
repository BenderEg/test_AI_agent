from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    BASE_API: str = "/api/v1"

    # Environment
    ENVIRONMENT: Literal["dev", "prod"] = "dev"

    # Swagger/OpenAPI
    SWAGGER_ENABLED: bool = True

    # Common

    GITHUB_TOKEN: str = "your token"
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "codebase"
    LLM_HOST: str = "ollama"
    LLM_PORT: int = 11434
    LLM_MODEL: str = "llama3"

    # Two-stage retrieval: vector search (bi-encoder) → Cross-Encoder reranking
    RERANKER_ENABLED: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # aiohttp session timeouts (seconds)
    HTTP_TIMEOUT_TOTAL: int = 30
    HTTP_TIMEOUT_CONNECT: int = 5

    @property
    def is_debug(self) -> bool:
        return self.ENVIRONMENT == "dev"

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    @property
    def llm_url(self) -> str:
        return f"http://{self.LLM_HOST}:{self.LLM_PORT}"


settings = Settings()
