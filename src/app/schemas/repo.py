from pydantic import BaseModel, Field, field_validator


class IngestRepo(BaseModel):
    owner: str
    repo: str
    branch: str = "main"
    force: bool = False


class QueryInfo(BaseModel):
    query: str
    limit: int | None = Field(default=3, ge=1, le=100)
    score_threshold: float | None = Field(default=0.2, ge=0.0, le=1.0)
    owner: str | None = Field(default=None, min_length=1)
    repo: str | None = Field(default=None, min_length=1)
    branch: str | None = "main"

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, repo: str | None, info) -> str | None:
        owner = info.data.get("owner")
        if repo and not owner:
            raise ValueError("'owner' is required when 'repo' is specified")
        return repo


class AskQueryInfo(QueryInfo):
    adapt_user_query: bool = False


class QueryResponseItem(BaseModel):
    file: str
    symbol: str
    code: str
    score: float = 0.0
    rerank_score: float | None = None


class QueryResponse(BaseModel):
    items: list[QueryResponseItem]
    total: int
    score_threshold_used: float | None


class AskResponse(BaseModel):
    answer: str
