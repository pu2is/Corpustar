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
