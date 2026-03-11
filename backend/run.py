from copy import deepcopy

import uvicorn
from uvicorn.config import LOGGING_CONFIG

from app.core.config import settings


def _build_log_config() -> dict:
    log_config = deepcopy(LOGGING_CONFIG)
    log_config["root"] = {"handlers": ["default"], "level": "INFO"}
    return log_config


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level="info",
        log_config=_build_log_config(),
    )
