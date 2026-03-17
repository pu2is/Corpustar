from collections.abc import Generator
from sqlite3 import Connection

from app.infrastructure.db.connection import connection_scope


def get_db_connection() -> Generator[Connection, None, None]:
    with connection_scope() as connection:
        yield connection
