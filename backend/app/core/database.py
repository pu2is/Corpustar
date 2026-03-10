from collections.abc import Generator
from sqlite3 import Connection, Row, connect

from app.core.config import settings


def initialize_database() -> None:
    settings.sqlite_database_path.parent.mkdir(parents=True, exist_ok=True)

    with _open_connection() as connection:
        connection.commit()


def get_connection() -> Generator[Connection, None, None]:
    connection = _open_connection()

    try:
        yield connection
    finally:
        connection.close()


def _open_connection() -> Connection:
    connection = connect(settings.sqlite_database_path)
    connection.row_factory = Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection
