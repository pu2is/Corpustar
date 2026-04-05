from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.root import router as root_router
from app.api.routes import router as api_router
from app.api.ws import router as ws_router
from app.core.config import settings
from app.infrastructure.db.bootstrap import ensure_database_ready


def create_app() -> FastAPI:
    app = FastAPI(title=settings.api_title)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(root_router)
    app.include_router(api_router, prefix="/api")
    app.include_router(ws_router)

    @app.on_event("startup")
    def _startup_database_bootstrap() -> None:
        ensure_database_ready()

    return app


app = create_app()
