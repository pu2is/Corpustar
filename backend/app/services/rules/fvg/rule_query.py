from app.infrastructure.repositories.fvg_entries import get_fvg_entries_by_rule_id
from app.infrastructure.repositories.rules import get_rule_by_id


def list_fvg_entries(rule_id: str) -> list[dict[str, str]]:
    parent_rule = get_rule_by_id(rule_id=rule_id)
    if parent_rule is None:
        raise FileNotFoundError(f"Rule not found: {rule_id}")
    if parent_rule["type"] != "fvg":
        raise ValueError(f"Rule {rule_id} is not type 'fvg'")

    return get_fvg_entries_by_rule_id(rule_id=rule_id)
