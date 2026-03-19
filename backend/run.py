import errno
import socket
import sys
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


def _ensure_port_available(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_socket:
        try:
            probe_socket.bind((host, port))
        except OSError as error:
            if error.errno == errno.EADDRINUSE or getattr(error, "winerror", None) == 10048:
                print(
                    f"Error: port {port} is already in use on {host}. "
                    f"Stop the existing process and retry.",
                    file=sys.stderr,
                )
                raise SystemExit(1) from error
            raise


if __name__ == "__main__":
    _ensure_port_available(settings.backend_host, settings.backend_port)
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
