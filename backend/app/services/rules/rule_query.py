from app.infrastructure.repositories.rules import (
    get_all_rules as get_all_rule_rows,
    get_rule_by_id,
)


def get_all_rules() -> list[dict]:
    return get_all_rule_rows()


def get_rule(rule_id: str) -> dict | None:
    return get_rule_by_id(rule_id)
