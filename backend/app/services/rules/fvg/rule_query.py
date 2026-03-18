from app.infrastructure.repositories.rules import get_rule_by_id
from app.infrastructure.repositories.rules_fvg import list_rule_fvg_rows_by_rule_id

FVG_RULE_TYPE = "fvg"


def _map_fvg_row_to_item(row: dict[str, str]) -> dict[str, str]:
    return {
        "id": row["id"],
        "ruleId": row["rule_id"],
        "verb": row["verb"],
        "phrase": row["phrase"],
    }


def list_fvg_rules(rule_id: str) -> list[dict]:
    parent_rule = get_rule_by_id(rule_id=rule_id)
    if parent_rule is None:
        raise FileNotFoundError(f"Rule not found: {rule_id}")
    if parent_rule["type"] != FVG_RULE_TYPE:
        raise ValueError(f"Rule {rule_id} is not type '{FVG_RULE_TYPE}'")

    rows = list_rule_fvg_rows_by_rule_id(rule_id=rule_id)
    return [_map_fvg_row_to_item(row) for row in rows]
