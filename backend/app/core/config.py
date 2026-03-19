import os
from pathlib import Path


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    return value


def _load_dotenv() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    env_files = [backend_dir / ".env", backend_dir / ".env.local"]

    for env_path in env_files:
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue

            os.environ[key] = _strip_wrapping_quotes(value.strip())


_load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.backend_dir = Path(__file__).resolve().parents[2]
        self.api_title = os.getenv("API_TITLE", "Corpustar API")
        self.backend_host = self._get_required("BACKEND_HOST")
        self.backend_port = self._get_int("BACKEND_PORT")
        self.frontend_origin = self._get_required("FRONTEND_ORIGIN")
        self.sqlite_database_path = Path(
            os.getenv("SQLITE_DATABASE_PATH",
                str(self.backend_dir / "data" / "corpustar.sqlite3"))
        ).resolve()
        self.default_sentence_per_page = self._get_int_or_default("DEFAULT_SENTENCE_PER_PAGE", 20)

    @staticmethod
    def _get_required(name: str) -> str:
        value = os.getenv(name)
        if value is None or not value.strip():
            raise ValueError(f"{name} is required (set it in backend/.env)")

        return value.strip()

    @staticmethod
    def _get_int_or_default(name: str, default: int) -> int:
        value = os.getenv(name)
        if value is None or not value.strip():
            return default
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc

    @classmethod
    def _get_int(cls, name: str) -> int:
        value = cls._get_required(name)

        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc

settings = Settings()
