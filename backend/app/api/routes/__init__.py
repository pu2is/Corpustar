from fastapi import APIRouter

from app.api.routes.documents import router as documents_router
from app.api.routes.process import router as process_router
from app.api.routes.sentence import router as sentence_router
from app.api.routes.rules import router as rules_router
from app.api.routes.rules_fvg import router as rules_fvg_router

router = APIRouter()
router.include_router(documents_router)
router.include_router(process_router)
router.include_router(sentence_router)
router.include_router(rules_router)
router.include_router(rules_fvg_router)