from uuid import uuid4

from app.core.process.fvg_entries.prelabel import FvgPrelabel
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.fvg_entries import (
    get_fvg_entry_by_id,
    modify_fvg_by_id,
    rm_fvg_entry_by_id,
    write_fvg_entry_item,
)
from app.infrastructure.repositories.rules import get_rule_by_id


_PRELABEL = FvgPrelabel()


def _validate_non_empty_text(field_name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def add_fvg_entry(
    *,
    rule_id: str,
    verb: str,
    phrase: str,
    noun: str | None = None,
    prep: str | None = None,
    structure_type: str | None = None,
    semantic_type: str | None = None,
) -> dict[str, str]:
    normalized_verb = _validate_non_empty_text("verb", verb)
    normalized_phrase = _validate_non_empty_text("phrase", phrase)

    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            parent_rule = get_rule_by_id(rule_id=rule_id, connection=connection)
            if parent_rule is None:
                raise FileNotFoundError(f"Rule not found: {rule_id}")
            if parent_rule["type"] != "fvg":
                raise ValueError(f"Rule {rule_id} is not type 'fvg'")

            if not all([noun, prep, structure_type, semantic_type]):
                prelabel = _PRELABEL.label([{"verb": normalized_verb, "phrase": normalized_phrase}])[0]
                noun = noun if noun is not None else prelabel["noun"]
                prep = prep if prep is not None else prelabel["prep"]
                structure_type = structure_type if structure_type is not None else prelabel["structure_type"]
                semantic_type = semantic_type if semantic_type is not None else prelabel["semantic_type"]

            inserted = write_fvg_entry_item(
                row={
                    "id": str(uuid4()),
                    "rule_id": rule_id,
                    "verb": normalized_verb,
                    "phrase": normalized_phrase,
                    "noun": str(noun or ""),
                    "prep": str(prep or ""),
                    "structure_type": str(structure_type or "prep"),
                    "semantic_type": str(semantic_type or "unknown"),
                },
                connection=connection,
            )

            connection.commit()
            return inserted
        except Exception:
            connection.rollback()
            raise


def remove_fvg_entry(fvg_id: str) -> dict[str, str]:
    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            existing = get_fvg_entry_by_id(fvg_id=fvg_id, connection=connection)
            if existing is None:
                raise FileNotFoundError(f"FVG entry not found: {fvg_id}")

            removed = rm_fvg_entry_by_id(fvg_id=fvg_id, connection=connection)
            if not removed:
                raise RuntimeError(f"Failed to remove FVG entry: {fvg_id}")

            connection.commit()
            return {
                "id": fvg_id,
                "rule_id": existing["rule_id"],
            }
        except Exception:
            connection.rollback()
            raise


def correct_fvg_entry(
    *,
    fvg_id: str,
    verb: str | None = None,
    phrase: str | None = None,
    noun: str | None = None,
    prep: str | None = None,
    structure_type: str | None = None,
    semantic_type: str | None = None,
) -> dict[str, str]:
    if verb is not None:
        verb = _validate_non_empty_text("verb", verb)
    if phrase is not None:
        phrase = _validate_non_empty_text("phrase", phrase)

    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")
            updated = modify_fvg_by_id(
                fvg_id,
                verb=verb,
                phrase=phrase,
                noun=noun,
                prep=prep,
                structure_type=structure_type,
                semantic_type=semantic_type,
                connection=connection,
            )
            connection.commit()
            return updated
        except Exception:
            connection.rollback()
            raise
