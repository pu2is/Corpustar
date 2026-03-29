from sqlalchemy import literal, select

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories._sqlalchemy import execute


def ping_database() -> None:
    with connection_scope() as connection:
        execute(connection, select(literal(1))).fetchone()
