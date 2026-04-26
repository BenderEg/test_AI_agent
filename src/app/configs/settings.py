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
    LLM_HOST: str = "qdrant"
    LLM_PORT: int = 11434
    LLM_MODEL: str = "ollama"

    @property
    def is_debug(self) -> bool:
        return self.ENVIRONMENT == "dev"
    
    @property
    def qdrant_url(self) -> bool:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
    
    @property
    def llm_url(self) -> bool:
        return f"http://{self.LLM_HOST}:{self.LLM_PORT}"


settings = Settings()