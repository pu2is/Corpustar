from typing import TypedDict
from uuid import uuid4

from app.core.rules.fvg_csv_reader import read_fvg_csv
from app.core.rules.rule_utils import calculate_rule_id, resolve_rule_path, validate_rule_type
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.rules import get_rule_by_id, insert_rule
from app.infrastructure.repositories.rules_fvg import bulk_insert_rule_fvg_rows


class ImportRuleResult(TypedDict):
    rule: dict[str, str]
    importedCount: int


def import_rule(path: str, rule_type: str = "fvg") -> ImportRuleResult:
    normalized_rule_type = validate_rule_type(rule_type)
    resolved_csv_path = resolve_rule_path(path)
    rule_id = calculate_rule_id(resolved_csv_path)

    rule = {
        "id": rule_id,
        "type": normalized_rule_type,
        "path": resolved_csv_path,
    }
    imported_fvg_rows: list[dict[str, str]] = []

    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            existing_rule = get_rule_by_id(rule_id=rule_id, connection=connection)
            if existing_rule is not None:
                raise ValueError(f"Rule already exists for hash: {rule_id}")

            parsed_rows = read_fvg_csv(resolved_csv_path)
            imported_fvg_rows = [
                {
                    "id": str(uuid4()),
                    "rule_id": rule_id,
                    "verb": row["verb"],
                    "phrase": row["phrase"],
                }
                for row in parsed_rows
            ]

            insert_rule(rule=rule, connection=connection)
            if imported_fvg_rows:
                bulk_insert_rule_fvg_rows(
                    rows=imported_fvg_rows,
                    connection=connection,
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return {
        "rule": rule,
        "importedCount": len(imported_fvg_rows),
    }
