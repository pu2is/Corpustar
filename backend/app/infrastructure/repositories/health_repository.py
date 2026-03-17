from app.infrastructure.db.connection import connection_scope


def ping_database() -> None:
    with connection_scope() as connection:
        connection.execute("SELECT 1").fetchone()
