from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.fvg_entries import rm_fvg_entries_by_rule_id
from app.infrastructure.repositories.processings import rm_process_item
from app.infrastructure.repositories.rules import get_rule_by_id, rm_rule_item


def remove_rule(rule_id: str) -> dict[str, str | int]:
    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")

            rule_item = get_rule_by_id(rule_id=rule_id, connection=connection)
            if rule_item is None:
                raise FileNotFoundError(f"Rule not found: {rule_id}")

            removed_fvg_count = 0
            if rule_item["type"] == "fvg":
                removed_fvg_count = rm_fvg_entries_by_rule_id(rule_id=rule_id, connection=connection)

            removed = rm_rule_item(rule_id=rule_id, connection=connection)
            if not removed:
                raise RuntimeError(f"Failed to remove rule: {rule_id}")

            rm_process_item(str(rule_item["version_id"]), connection=connection)

            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return {
        "id": rule_id,
        "removed_fvg_count": removed_fvg_count,
    }
