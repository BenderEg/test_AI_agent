from pydantic import BaseModel, field_validator


class IngestRepo(BaseModel):
    owner: str
    repo: str
    branch: str


class QueryInfo(BaseModel):
    query: str
    limit: int | None = 3
    score_threshold: float | None = 0.3
    owner: str | None = None
    repo: str | None = None
    branch: str | None = "master"

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, repo, info):
        owner = info.data.get("owner")
        if repo and not owner:
            raise ValueError("При указании репозитория должен быть передан 'owner'")
        return repo


class AskQueryInfo(QueryInfo):
    adapt_user_query: bool = False


class QueryResponseItem(BaseModel):
    file: str
    symbol: str
    code: str


class QueryResponse(BaseModel):
    items: list[QueryResponseItem]
