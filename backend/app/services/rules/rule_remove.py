from typing import TypedDict

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.rules import (
    get_rule_by_id,
    remove_rule as remove_rule_row,
)
from app.infrastructure.repositories.rules_fvg import list_rule_fvg_rows_by_rule_id


class RemoveRuleResult(TypedDict):
    id: str
    removedFvgCount: int


def remove_rule(rule_id: str) -> RemoveRuleResult:
    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            existing_rule = get_rule_by_id(rule_id=rule_id, connection=connection)
            if existing_rule is None:
                raise FileNotFoundError(f"Rule not found: {rule_id}")

            removed_fvg_count = len(
                list_rule_fvg_rows_by_rule_id(rule_id=rule_id, connection=connection)
            )
            is_removed = remove_rule_row(rule_id=rule_id, connection=connection)
            if not is_removed:
                raise RuntimeError(f"Failed to remove rule from database: {rule_id}")

            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return {
        "id": rule_id,
        "removedFvgCount": removed_fvg_count,
    }
