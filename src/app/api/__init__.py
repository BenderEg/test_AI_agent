from fastapi import APIRouter

from src.app.configs.settings import settings
from src.app.api.repo_parser import router as repo_parser_router


router = APIRouter(prefix=settings.BASE_API)

router.include_router(repo_parser_router)