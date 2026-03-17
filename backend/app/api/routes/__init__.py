from fastapi import APIRouter

from app.api.routes.documents import router as documents_router
from app.api.routes.process import router as process_router
from app.api.routes.sentence import router as sentence_router

router = APIRouter()
router.include_router(documents_router)
router.include_router(process_router)
router.include_router(sentence_router)
