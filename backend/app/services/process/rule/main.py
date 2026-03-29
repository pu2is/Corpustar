from app.infrastructure.repositories.processings import (
    change_process_item_state,
    map_process_row_to_item,
    write_process_item,
)
from app.services.process.rule.save_fvg_entries import save_fvg_entries
from app.socket.socket_events import (
    IMPORT_FVG_ENTRIES_SUCCEED,
    IMPORT_RULE_FAILED,
    IMPORT_RULE_STARTED,
    IMPORT_RULE_SUCCEED,
)
from app.socket.socket_publisher import publish_best_effort


def import_rule(request: dict[str, str]) -> dict[str, object]:
    rule_type = str(request.get("type", "")).strip().lower()
    path = str(request.get("path", "")).strip()
    if not path:
        raise ValueError("path is required")
    if rule_type != "fvg":
        raise ValueError(f"Unsupported import rule type: {rule_type}")

    process = write_process_item(
        doc_id=None,
        type="import_rule",
        state="running",
        meta={"process": "import_rule_fvg", "path": path},
    )
    process_id = str(process["id"])
    publish_best_effort(IMPORT_RULE_STARTED, map_process_row_to_item(process))

    try:
        saved = save_fvg_entries(
            process_id=process_id,
            path=path,
            rule_type=rule_type,
        )

        succeeded = change_process_item_state(process_id, "succeed")
        process_item = map_process_row_to_item(succeeded)
        publish_best_effort(
            IMPORT_RULE_SUCCEED,
            {
                "processing": process_item,
                "rule": saved["rule"],
            },
        )
        publish_best_effort(IMPORT_FVG_ENTRIES_SUCCEED, {"ok": True})

        return {
            "processing": process_item,
            "rule": saved["rule"],
        }

    except Exception as error:
        failed = change_process_item_state(
            process_id,
            "failed",
            error_message=str(error),
        )
        publish_best_effort(IMPORT_RULE_FAILED, map_process_row_to_item(failed))
        raise
