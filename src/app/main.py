from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.adapters.http_session import close_client_session, init_client_session
from src.app.adapters.vectored import QdrantAdapter
from src.app.api import router
from src.app.configs.settings import settings
from src.app.utils.embedder import embed
from src.app.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Start up application ...")
    await init_client_session()
    vector_adapter = QdrantAdapter(embeder=embed)
    await vector_adapter.on_start_up()
    app.state.vector_adapter = vector_adapter
    yield
    logger.info("Shut down application ...")
    await vector_adapter.on_shut_down()
    await close_client_session()

    
app = FastAPI(
    title="Github repo rapser API",
    version="0.1.0",
    debug=settings.is_debug,
    docs_url="/docs" if settings.SWAGGER_ENABLED else None,
    redoc_url="/redoc" if settings.SWAGGER_ENABLED else None,
    lifespan=lifespan,
)

app.include_router(router)