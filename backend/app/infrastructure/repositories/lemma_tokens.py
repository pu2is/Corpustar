from collections.abc import Iterable, Mapping
from sqlite3 import Connection
from typing import Any

from sqlalchemy import bindparam, delete, func, insert, select

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories._sqlalchemy import (
    execute,
    execute_many,
    lemma_tokens_table,
)

LemmaTokenRow = dict[str, int | str]

def _string_value(row: Mapping[str, Any], key: str) -> str:
    value = row[key]
    if value is None:
        return ""
    return str(value)


def _int_value(row: Mapping[str, Any], key: str) -> int:
    value = row[key]
    if value is None:
        return 0
    return int(value)


def _map_lemma_token_row(row: Mapping[str, Any]) -> LemmaTokenRow:
    return {
        "id": _string_value(row, "id"),
        "version_id": _string_value(row, "version_id"),
        "sentence_id": _string_value(row, "sentence_id"),
        "source_word": _string_value(row, "source_word"),
        "lemma_word": _string_value(row, "lemma_word"),
        "word_index": _int_value(row, "word_index"),
        "head_index": _int_value(row, "head_index"),
        "pos_tag": _string_value(row, "pos_tag"),
        "fine_pos_tag": _string_value(row, "fine_pos_tag"),
        "morph": _string_value(row, "morph"),
        "dependency_relationship": _string_value(row, "dependency_relationship"),
    }


def save_lemma_token_in_batch(
    tokens: Iterable[Mapping[str, int | str]],
    clear_existing: bool = False,
    connection: Connection | None = None,
) -> None:
    normalized_rows = [_normalize_lemma_token_row(token) for token in tokens]
    if not normalized_rows:
        return

    version_id = str(normalized_rows[0]["version_id"])

    if connection is None:
        with connection_scope() as scoped_connection:
            save_lemma_token_in_batch(
                normalized_rows,
                clear_existing=clear_existing,
                connection=scoped_connection,
            )
            scoped_connection.commit()
        return

    if clear_existing:
        execute(
            connection,
            delete(lemma_tokens_table).where(lemma_tokens_table.c.version_id == version_id),
        )

    statement = insert(lemma_tokens_table).prefix_with("OR REPLACE").values(
        id=bindparam("id"),
        version_id=bindparam("version_id"),
        sentence_id=bindparam("sentence_id"),
        source_word=bindparam("source_word"),
        lemma_word=bindparam("lemma_word"),
        word_index=bindparam("word_index"),
        head_index=bindparam("head_index"),
        pos_tag=bindparam("pos_tag"),
        fine_pos_tag=bindparam("fine_pos_tag"),
        morph=bindparam("morph"),
        dependency_relationship=bindparam("dependency_relationship"),
    )
    execute_many(connection, statement, normalized_rows)


def get_lemma_tokens_by_ids(lemma_ids: list[str]) -> dict[str, LemmaTokenRow]:
    if not lemma_ids:
        return {}

    unique_ids = list(dict.fromkeys(lemma_ids))
    statement = (
        select(
            lemma_tokens_table.c.id,
            lemma_tokens_table.c.version_id,
            lemma_tokens_table.c.sentence_id,
            lemma_tokens_table.c.source_word,
            lemma_tokens_table.c.lemma_word,
            lemma_tokens_table.c.word_index,
            lemma_tokens_table.c.head_index,
            lemma_tokens_table.c.pos_tag,
            lemma_tokens_table.c.fine_pos_tag,
            lemma_tokens_table.c.morph,
            lemma_tokens_table.c.dependency_relationship,
        )
        .select_from(lemma_tokens_table)
        .where(lemma_tokens_table.c.id.in_(unique_ids))
    )

    with connection_scope() as connection:
        rows = execute(connection, statement).fetchall()

    return {str(row["id"]): _map_lemma_token_row(row) for row in rows}


def read_lemma_tokens_by_sentence_ids(sentence_ids: list[str]) -> dict[str, list[LemmaTokenRow]]:
    if not sentence_ids:
        return {}

    unique_sentence_ids = [sentence_id for sentence_id in dict.fromkeys(sentence_ids)]
    statement = (
        select(
            lemma_tokens_table.c.id,
            lemma_tokens_table.c.version_id,
            lemma_tokens_table.c.sentence_id,
            lemma_tokens_table.c.source_word,
            lemma_tokens_table.c.lemma_word,
            lemma_tokens_table.c.word_index,
            lemma_tokens_table.c.head_index,
            lemma_tokens_table.c.pos_tag,
            lemma_tokens_table.c.fine_pos_tag,
            lemma_tokens_table.c.morph,
            lemma_tokens_table.c.dependency_relationship,
        )
        .select_from(lemma_tokens_table)
        .where(lemma_tokens_table.c.sentence_id.in_(unique_sentence_ids))
        .order_by(lemma_tokens_table.c.sentence_id.asc(), lemma_tokens_table.c.word_index.asc())
    )

    with connection_scope() as connection:
        rows = execute(connection, statement).fetchall()

    result: dict[str, list[LemmaTokenRow]] = {sentence_id: [] for sentence_id in unique_sentence_ids}
    for row in rows:
        mapped_row = _map_lemma_token_row(row)
        sentence_id = str(mapped_row["sentence_id"])
        result.setdefault(sentence_id, []).append(mapped_row)

    return result


def rm_lemma_tokens_by_version_id(version_id: str, connection: Connection | None = None) -> int:
    if connection is None:
        with connection_scope() as scoped_connection:
            removed = rm_lemma_tokens_by_version_id(version_id, connection=scoped_connection)
            scoped_connection.commit()
            return removed

    cursor = execute(
        connection,
        delete(lemma_tokens_table).where(lemma_tokens_table.c.version_id == version_id),
    )
    return cursor.rowcount


def count_lemma_tokens_by_version_id(version_id: str, connection: Connection | None = None) -> int:
    statement = select(func.count()).select_from(lemma_tokens_table).where(
        lemma_tokens_table.c.version_id == version_id
    )

    if connection is None:
        with connection_scope() as scoped_connection:
            return count_lemma_tokens_by_version_id(version_id, connection=scoped_connection)

    row = execute(connection, statement).fetchone()
    if row is None:
        return 0
    return int(row[0])


def get_num_lemma_by_id_and_pos(
    version_id: str,
    pos: str,
    connection: Connection | None = None,
) -> int:
    statement = (
        select(func.count())
        .select_from(lemma_tokens_table)
        .where(
            (lemma_tokens_table.c.version_id == version_id)
            & (lemma_tokens_table.c.pos_tag == pos)
        )
    )
    if connection is None:
        with connection_scope() as scoped_connection:
            return get_num_lemma_by_id_and_pos(version_id, pos, connection=scoped_connection)
    row = execute(connection, statement).fetchone()
    return int(row[0]) if row else 0


def _normalize_lemma_token_row(row: Mapping[str, int | str]) -> LemmaTokenRow:
    return {
        "id": str(row["id"]),
        "version_id": str(row["version_id"]),
        "sentence_id": str(row["sentence_id"]),
        "source_word": str(row["source_word"]),
        "lemma_word": str(row["lemma_word"]),
        "word_index": int(row["word_index"]),
        "head_index": int(row["head_index"]),
        "pos_tag": str(row["pos_tag"]),
        "fine_pos_tag": str(row["fine_pos_tag"]),
        "morph": str(row["morph"]),
        "dependency_relationship": str(row["dependency_relationship"]),
    }
