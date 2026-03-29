from typing import TypedDict

from app.services.process.rule.main import import_rule as run_import_rule_process


class ImportRuleResult(TypedDict):
    rule: dict[str, str]
    importedCount: int


def import_rule(path: str, rule_type: str = "fvg") -> ImportRuleResult:
    response = run_import_rule_process(
        {
            "path": path,
            "type": rule_type,
        }
    )
    return {
        "rule": response["rule"],  # type: ignore[index]
        "importedCount": len(response["fvg_entries"]),  # type: ignore[index]
    }
