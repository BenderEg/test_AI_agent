from aiohttp import ClientSession, ClientTimeout
from src.app.configs.settings import settings

session: ClientSession | None = None


class SessionNotInitializedError(Exception):
    pass


async def get_aiohttp_session() -> ClientSession:
    if not session:
        raise SessionNotInitializedError
    return session


async def init_client_session() -> None:
    global session
    # Per-call overrides (e.g. OllamaAdapter's 150s timeout) take precedence over this
    # session-level default — aiohttp uses the per-request timeout when specified.
    session = ClientSession(
        timeout=ClientTimeout(total=settings.HTTP_TIMEOUT_TOTAL, connect=settings.HTTP_TIMEOUT_CONNECT),
    )


async def close_client_session() -> None:
    global session
    if session is not None:
        await session.close()
