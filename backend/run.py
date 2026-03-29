from copy import deepcopy

import uvicorn
from uvicorn.config import LOGGING_CONFIG

from app.core.config import settings


def _build_log_config() -> dict:
    log_config = deepcopy(LOGGING_CONFIG)
    log_config["root"] = {"handlers": ["default"], "level": "INFO"}
    return log_config


def _build_reload_dirs() -> list[str]:
    return ["app"]


def _build_reload_excludes() -> list[str]:
    return [
        "data",
        "data/*.sqlite3",
        "data/*.sqlite3-*",
        "data/*.db",
        "data/*.db-*",
    ]


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        reload_dirs=_build_reload_dirs(),
        reload_excludes=_build_reload_excludes(),
        log_level="info",
        log_config=_build_log_config(),
    )
