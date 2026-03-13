from app.core.db import get_connection


def insert_document(doc: dict) -> None:
    connection_generator = get_connection()
    connection = next(connection_generator)

    try:
        connection.execute(
            """
            INSERT INTO documents (
                id,
                filename,
                display_name,
                note,
                source_path,
                text_path,
                text_char_count,
                file_type,
                file_size,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc["id"],
                doc["filename"],
                doc["displayName"],
                doc["note"],
                doc["sourcePath"],
                doc["textPath"],
                doc["textCharCount"],
                doc["fileType"],
                doc["fileSize"],
                doc["createdAt"],
                doc["updatedAt"],
            ),
        )
        connection.commit()
    finally:
        connection_generator.close()


def get_all_documents() -> list[dict]:
    connection_generator = get_connection()
    connection = next(connection_generator)

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                filename,
                display_name,
                note,
                source_path,
                text_path,
                text_char_count,
                file_type,
                file_size,
                created_at,
                updated_at
            FROM documents
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [
            {
                "id": row["id"],
                "filename": row["filename"],
                "displayName": row["display_name"],
                "note": row["note"],
                "sourcePath": row["source_path"],
                "textPath": row["text_path"],
                "textCharCount": row["text_char_count"],
                "fileType": row["file_type"],
                "fileSize": row["file_size"],
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]
    finally:
        connection_generator.close()


def get_document_by_id(document_id: str) -> dict | None:
    connection_generator = get_connection()
    connection = next(connection_generator)

    try:
        row = connection.execute(
            """
            SELECT
                id,
                filename,
                display_name,
                note,
                source_path,
                text_path,
                text_char_count,
                file_type,
                file_size,
                created_at,
                updated_at
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "filename": row["filename"],
            "displayName": row["display_name"],
            "note": row["note"],
            "sourcePath": row["source_path"],
            "textPath": row["text_path"],
            "textCharCount": row["text_char_count"],
            "fileType": row["file_type"],
            "fileSize": row["file_size"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }
    finally:
        connection_generator.close()


def remove_document(document_id: str) -> bool:
    connection_generator = get_connection()
    connection = next(connection_generator)

    try:
        cursor = connection.execute(
            """
            DELETE FROM documents
            WHERE id = ?
            """,
            (document_id,),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection_generator.close()
