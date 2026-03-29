from app.infrastructure.repositories.rules import get_rule_by_id, read_all_rules


def get_all_rules() -> list[dict[str, str]]:
    return read_all_rules()


def get_rule(rule_id: str) -> dict[str, str] | None:
    return get_rule_by_id(rule_id)
