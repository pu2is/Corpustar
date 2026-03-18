from uuid import uuid4

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.rules import get_rule_by_id
from app.infrastructure.repositories.rules_fvg import (
    get_rule_fvg_row_by_id,
    insert_rule_fvg_row,
    remove_rule_fvg_row,
    update_rule_fvg_row,
)

FVG_RULE_TYPE = "fvg"


def _validate_non_empty_text(field_name: str, value: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} is required")
    return normalized_value


def _map_fvg_row_to_item(row: dict[str, str]) -> dict[str, str]:
    return {
        "id": row["id"],
        "ruleId": row["rule_id"],
        "verb": row["verb"],
        "phrase": row["phrase"],
    }


def add_fvg_rule(rule_id: str, verb: str, phrase: str) -> dict:
    normalized_verb = _validate_non_empty_text("verb", verb)
    normalized_phrase = _validate_non_empty_text("phrase", phrase)

    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            parent_rule = get_rule_by_id(rule_id=rule_id, connection=connection)
            if parent_rule is None:
                raise FileNotFoundError(f"Rule not found: {rule_id}")
            if parent_rule["type"] != FVG_RULE_TYPE:
                raise ValueError(f"Rule {rule_id} is not type '{FVG_RULE_TYPE}'")

            inserted_row = insert_rule_fvg_row(
                row={
                    "id": str(uuid4()),
                    "rule_id": rule_id,
                    "verb": normalized_verb,
                    "phrase": normalized_phrase,
                },
                connection=connection,
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return _map_fvg_row_to_item(inserted_row)


def remove_fvg_rule(fvg_rule_id: str) -> dict:
    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            target_row = get_rule_fvg_row_by_id(
                rule_fvg_id=fvg_rule_id,
                connection=connection,
            )
            if target_row is None:
                raise FileNotFoundError(f"FVG rule row not found: {fvg_rule_id}")

            is_removed = remove_rule_fvg_row(
                rule_fvg_id=fvg_rule_id,
                connection=connection,
            )
            if not is_removed:
                raise RuntimeError(f"Failed to remove FVG rule row: {fvg_rule_id}")

            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return {
        "id": fvg_rule_id,
        "ruleId": target_row["rule_id"],
    }


def modify_fvg_rule(fvg_rule_id: str, verb: str, phrase: str) -> dict:
    normalized_verb = _validate_non_empty_text("verb", verb)
    normalized_phrase = _validate_non_empty_text("phrase", phrase)

    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            existing_row = get_rule_fvg_row_by_id(
                rule_fvg_id=fvg_rule_id,
                connection=connection,
            )
            if existing_row is None:
                raise FileNotFoundError(f"FVG rule row not found: {fvg_rule_id}")

            updated_row = update_rule_fvg_row(
                rule_fvg_id=fvg_rule_id,
                verb=normalized_verb,
                phrase=normalized_phrase,
                connection=connection,
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return _map_fvg_row_to_item(updated_row)
