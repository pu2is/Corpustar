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
                file_type,
                file_size,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc["id"],
                doc["filename"],
                doc["displayName"],
                doc["note"],
                doc["sourcePath"],
                doc["textPath"],
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
                "fileType": row["file_type"],
                "fileSize": row["file_size"],
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]
    finally:
        connection_generator.close()
