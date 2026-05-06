from fastapi import APIRouter
from src.app.api.health import router as health_router
from src.app.api.repo_parser import router as repo_parser_router
from src.app.configs.settings import settings

router = APIRouter(prefix=settings.BASE_API)

router.include_router(health_router)
router.include_router(repo_parser_router)
