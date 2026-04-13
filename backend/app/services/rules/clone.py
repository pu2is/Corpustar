import uuid
from pathlib import Path

from app.core.log import get_logger, log_event
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
    
    # Get the original rule
    original_rule = get_rule_by_id(rule_id)
    if original_rule is None:
        raise FileNotFoundError(f"Rule not found: {rule_id}")

    # Generate new id (uuid), keep version_id and type
    # Keeping version_id allows cloned rule to share same FVG rule set
    # Deletion logic will check if other rules use version_id before cleanup
    new_id = str(uuid.uuid4())
    new_version_id = original_rule["version_id"]
    rule_type = original_rule["type"]
    
    # Modify path: Clone:/[CLONE] ${file_name}.csv
    original_path = original_rule["path"]
    file_name = Path(original_path).stem  # Get filename without extension
    new_path = f"Clone:/[CLONE] {file_name}.csv"
    
    # Create cloned rule dict
    cloned_rule = {
        "id": new_id,
        "version_id": new_version_id,
        "type": rule_type,
        "path": new_path,
    }
    
    # Write to database
    try:
        written = write_rule_item(cloned_rule)
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            original_rule_id=rule_id,
            new_rule_id=new_id,
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
