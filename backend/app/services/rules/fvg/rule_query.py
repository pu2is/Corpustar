from app.infrastructure.repositories.fvg_entries import (
    filter_fvg_entry_by_rule_and_verb,
    get_fvg_entries_by_rule_id,
)
from app.infrastructure.repositories.rules import get_rule_by_id


def list_fvg_entries(rule_id: str) -> list[dict[str, str]]:
    parent_rule = get_rule_by_id(rule_id=rule_id)
    if parent_rule is None:
        raise FileNotFoundError(f"Rule not found: {rule_id}")
    if parent_rule["type"] != "fvg":
        raise ValueError(f"Rule {rule_id} is not type 'fvg'")

    return get_fvg_entries_by_rule_id(rule_id=rule_id)


def get_fvg_entry_by_rule_id_and_verb(rule_id: str, verb: str) -> list[dict[str, str]]:
    parent_rule = get_rule_by_id(rule_id=rule_id)
    if parent_rule is None:
        raise FileNotFoundError(f"Rule not found: {rule_id}")
    if parent_rule["type"] != "fvg":
        raise ValueError(f"Rule {rule_id} is not type 'fvg'")

    return filter_fvg_entry_by_rule_and_verb(rule_id=rule_id, verb=verb)
