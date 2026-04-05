from collections.abc import Iterable, Mapping
from sqlite3 import Connection
from typing import Any

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.dialects import sqlite
from sqlalchemy.sql import ClauseElement

metadata = MetaData()

documents_table = Table(
    "documents",
    metadata,
    Column("id", String, primary_key=True),
    Column("filename", String),
    Column("display_name", String),
    Column("note", String),
    Column("source_path", String),
    Column("text_path", String),
    Column("char_count", Integer),
    Column("file_type", String),
    Column("file_size", Integer),
    Column("created_at", String),
    Column("updated_at", String),
)

processings_table = Table(
    "processings",
    metadata,
    Column("id", String, primary_key=True),
    Column("parent_id", String),
    Column("doc_id", String),
    Column("type", String),
    Column("state", String),
    Column("created_at", String),
    Column("updated_at", String),
    Column("error_message", String),
    Column("meta_json", String),
)

sentences_table = Table(
    "sentences",
    metadata,
    Column("id", String, primary_key=True),
    Column("version_id", String),
    Column("doc_id", String),
    Column("start_offset", Integer),
    Column("end_offset", Integer),
    Column("source_text", String),
    Column("corrected_text", String),
)

lemma_tokens_table = Table(
    "lemma_tokens",
    metadata,
    Column("id", String, primary_key=True),
    Column("version_id", String),
    Column("sentence_id", String),
    Column("source_word", String),
    Column("lemma_word", String),
    Column("word_index", Integer),
    Column("head_index", Integer),
    Column("pos_tag", String),
    Column("fine_pos_tag", String),
    Column("morph", String),
    Column("dependency_relationship", String),
)

rules_table = Table(
    "rules",
    metadata,
    Column("id", String, primary_key=True),
    Column("version_id", String),
    Column("type", String),
    Column("path", String),
)

fvg_entries_table = Table(
    "fvg_entries",
    metadata,
    Column("id", String, primary_key=True),
    Column("rule_id", String),
    Column("verb", String),
    Column("phrase", String),
    Column("noun", String),
    Column("prep", String),
    Column("structure_type", String),
    Column("semantic_type", String),
)

fvg_candidates_table = Table(
    "fvg_candidates",
    metadata,
    Column("id", String, primary_key=True),
    Column("sentence_id", String),
    Column("algo_fvg_entry_id", String),
    Column("corrected_fvg_entry_id", String),
    Column("algo_verb_token", String),
    Column("algo_verb_index", Integer),
    Column("corrected_verb_token", String),
    Column("corrected_verb_index", Integer),
    Column("algo_noun_token", String),
    Column("algo_noun_index", Integer),
    Column("corrected_noun_token", String),
    Column("corrected_noun_index", Integer),
    Column("algo_prep_token", String),
    Column("algo_prep_index", Integer),
    Column("corrected_prep_token", String),
    Column("corrected_prep_index", Integer),
    Column("label", String),
    Column("manuelle_created", Integer),
    Column("removed", Integer),
)

_SQLITE_DIALECT = sqlite.dialect(paramstyle="qmark")


def execute(connection: Connection, statement: ClauseElement):
    sql, parameters = compile_statement(statement)
    return connection.execute(sql, parameters)


def execute_many(
    connection: Connection,
    statement: ClauseElement,
    rows: Iterable[Mapping[str, Any]],
) -> None:
    sql, parameter_names = compile_statement_for_many(statement)
    parameter_rows = [
        tuple(row.get(parameter_name) for parameter_name in parameter_names)
        for row in rows
    ]
    if not parameter_rows:
        return
    connection.executemany(sql, parameter_rows)


def compile_statement(statement: ClauseElement) -> tuple[str, tuple[Any, ...]]:
    compiled = statement.compile(
        dialect=_SQLITE_DIALECT,
        compile_kwargs={"render_postcompile": True},
    )
    position_names = list(getattr(compiled, "positiontup", ()) or ())
    parameters = compiled.params
    ordered_parameters = tuple(parameters[name] for name in position_names)
    return str(compiled), ordered_parameters


def compile_statement_for_many(statement: ClauseElement) -> tuple[str, tuple[str, ...]]:
    compiled = statement.compile(dialect=_SQLITE_DIALECT)
    position_names = tuple(getattr(compiled, "positiontup", ()) or ())
    return str(compiled), position_names
