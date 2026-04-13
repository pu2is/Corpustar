import uuid
from pathlib import Path

from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.fvg_entries import (
    get_fvg_entries_by_rule_id,
    save_fvg_entries_in_batch,
)
from app.infrastructure.repositories.rules import get_rule_by_id, write_rule_item

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def do_clone_rule(rule_id: str) -> dict[str, str]:
    """
    Clone a rule by duplicating it with a new id and modified path.
    
    Args:
        rule_id: The id of the rule to clone
        
    Returns:
        The cloned rule item as a dict with keys: id, version_id, type, path
        
    Raises:
        FileNotFoundError: If the rule_id does not exist
    """
    function_name = "do_clone_rule"
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE, function_name=function_name, rule_id=rule_id)

    try:
        with connection_scope() as connection:
            connection.execute("BEGIN")

            original_rule = get_rule_by_id(rule_id=rule_id, connection=connection)
            if original_rule is None:
                raise FileNotFoundError(f"Rule not found: {rule_id}")

            new_id = str(uuid.uuid4())
            cloned_rule = {
                "id": new_id,
                "version_id": str(original_rule["version_id"]),
                "type": str(original_rule["type"]),
                "path": f"Clone:/[CLONE] {Path(str(original_rule['path'])).stem}.csv",
            }

            written = write_rule_item(cloned_rule, connection=connection)

            cloned_fvg_count = 0
            if written["type"] == "fvg":
                source_entries = get_fvg_entries_by_rule_id(rule_id=rule_id, connection=connection)
                if source_entries:
                    cloned_entries = [
                        {
                            "id": str(uuid.uuid4()),
                            "rule_id": new_id,
                            "verb": entry["verb"],
                            "phrase": entry["phrase"],
                            "noun": entry["noun"],
                            "prep": entry["prep"],
                            "structure_type": entry["structure_type"],
                            "semantic_type": entry["semantic_type"],
                        }
                        for entry in source_entries
                    ]
                    save_fvg_entries_in_batch(cloned_entries, connection=connection)
                    cloned_fvg_count = len(cloned_entries)

            connection.commit()

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            original_rule_id=rule_id,
            new_rule_id=new_id,
            cloned_fvg_count=cloned_fvg_count,
        )
        return written
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=rule_id,
            error=str(error),
            exc_info=True,
        )
        raise
