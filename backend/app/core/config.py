import os
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        self.backend_dir = Path(__file__).resolve().parents[2]
        self.api_title = os.getenv("API_TITLE", "Corpustar API")
        self.backend_host = os.getenv("BACKEND_HOST", "127.0.0.1")
        self.backend_port = self._get_int("BACKEND_PORT", 619)
        self.frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:407")
        self.sqlite_database_path = Path(
            os.getenv(
                "SQLITE_DATABASE_PATH",
                str(self.backend_dir / "data" / "corpustar.sqlite3"),
            )
        ).resolve()

    @staticmethod
    def _get_int(name: str, default: int) -> int:
        value = os.getenv(name)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc


settings = Settings()
