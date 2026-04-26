from typing import Annotated

from aiohttp import ClientSession
from fastapi import Depends, Request

from src.app.adapters.http_session import get_aiohttp_session
from src.app.adapters.github_parser import GitHubParser
from src.app.adapters.llm import OllamaAdapter
from src.app.adapters.vectored import QdrantAdapter
from src.app.utils.embedder import embed


def get_github_parser(
    session: ClientSession = Depends(get_aiohttp_session),
) -> GitHubParser:
    return GitHubParser(session=session)

def get_vector_adapter(request: Request) -> QdrantAdapter:
    return request.app.state.vector_adapter

def get_llm_adapter(
    session: ClientSession = Depends(get_aiohttp_session),
) -> OllamaAdapter:
    return OllamaAdapter(session=session)


vector_adapter = Annotated[QdrantAdapter, Depends(get_vector_adapter)]
github_parser = Annotated[GitHubParser, Depends(get_github_parser)]
llm_adapter = Annotated[OllamaAdapter, Depends(get_llm_adapter)]