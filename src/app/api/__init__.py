from fastapi import APIRouter
from src.app.api.repo_parser import router as repo_parser_router
from src.app.configs.settings import settings

router = APIRouter(prefix=settings.BASE_API)

router.include_router(repo_parser_router)
