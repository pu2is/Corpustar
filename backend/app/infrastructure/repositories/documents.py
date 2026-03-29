from collections.abc import Mapping

from sqlalchemy import delete, insert, select

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories._sqlalchemy import documents_table, execute

DocumentRow = dict[str, int | str]


def write_document(document: DocumentRow) -> None:
    values = {
        "id": str(document["id"]),
        "filename": str(document["filename"]),
        "display_name": str(document["display_name"]),
        "note": str(document["note"]),
        "source_path": str(document["source_path"]),
        "text_path": str(document["text_path"]),
        "char_count": int(document["char_count"]),
        "file_type": str(document["file_type"]),
        "file_size": int(document["file_size"]),
        "created_at": str(document["created_at"]),
        "updated_at": str(document["updated_at"]),
    }
    with connection_scope() as connection:
        execute(connection, insert(documents_table).values(**values))
        connection.commit()


def read_all_documents() -> list[DocumentRow]:
    statement = (
        select(
            documents_table.c.id,
            documents_table.c.filename,
            documents_table.c.display_name,
            documents_table.c.note,
            documents_table.c.source_path,
            documents_table.c.text_path,
            documents_table.c.char_count,
            documents_table.c.file_type,
            documents_table.c.file_size,
            documents_table.c.created_at,
            documents_table.c.updated_at,
        )
        .select_from(documents_table)
        .order_by(documents_table.c.created_at.desc())
    )
    with connection_scope() as connection:
        rows = execute(connection, statement).fetchall()

    return [_map_document_row(row) for row in rows]


def read_document_by_id(document_id: str) -> DocumentRow | None:
    statement = (
        select(
            documents_table.c.id,
            documents_table.c.filename,
            documents_table.c.display_name,
            documents_table.c.note,
            documents_table.c.source_path,
            documents_table.c.text_path,
            documents_table.c.char_count,
            documents_table.c.file_type,
            documents_table.c.file_size,
            documents_table.c.created_at,
            documents_table.c.updated_at,
        )
        .select_from(documents_table)
        .where(documents_table.c.id == document_id)
    )
    with connection_scope() as connection:
        row = execute(connection, statement).fetchone()

    if row is None:
        return None
    return _map_document_row(row)


def rm_document(document_id: str) -> bool:
    with connection_scope() as connection:
        cursor = execute(
            connection,
            delete(documents_table).where(documents_table.c.id == document_id),
        )
        connection.commit()
    return cursor.rowcount > 0


def _map_document_row(row_map: Mapping[str, object]) -> DocumentRow:
    return {
        "id": str(row_map["id"]),
        "filename": str(row_map["filename"]),
        "display_name": str(row_map["display_name"]),
        "note": str(row_map["note"]),
        "source_path": str(row_map["source_path"]),
        "text_path": str(row_map["text_path"]),
        "char_count": int(row_map["char_count"]),
        "file_type": str(row_map["file_type"]),
        "file_size": int(row_map["file_size"]),
        "created_at": str(row_map["created_at"]),
        "updated_at": str(row_map["updated_at"]),
    }
