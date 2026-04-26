from aiohttp import ClientSession, ClientTimeout

session: ClientSession | None = None


class SessionNotInitializedError(Exception):
    pass


async def get_aiohttp_session() -> ClientSession:
    if not session:
        raise SessionNotInitializedError
    return session


async def init_client_session() -> None:
    global session
    session = ClientSession(
        timeout=ClientTimeout(total=2),
    )


async def close_client_session() -> None:
    global session
    await session.close()