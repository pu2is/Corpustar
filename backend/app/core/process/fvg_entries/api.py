from app.services.rules.fvg.modify_rule import add_fvg_entry, correct_fvg_entry, remove_fvg_entry
from app.services.rules.fvg.rule_query import list_fvg_entries
from app.socket.socket_events import FVG_APPENDED, FVG_REMOVED, FVG_UPDATED
from app.socket.socket_publisher import publish


def list_fvg_entry_items(rule_id: str) -> list[dict[str, str]]:
    return list_fvg_entries(rule_id=rule_id)


async def append_fvg_entry(
    *,
    rule_id: str,
    verb: str,
    phrase: str,
    noun: str,
    prep: str,
    structure_type: str,
    semantic_type: str,
) -> dict[str, str]:
    response = add_fvg_entry(
        rule_id=rule_id,
        verb=verb,
        phrase=phrase,
        noun=noun,
        prep=prep,
        structure_type=structure_type,
        semantic_type=semantic_type,
    )

    try:
        await publish(FVG_APPENDED, response)
    except Exception:
        pass

    return response


async def delete_fvg_entry(fvg_id: str) -> dict[str, object]:
    response = remove_fvg_entry(fvg_id=fvg_id)

    try:
        await publish(FVG_REMOVED, response)
    except Exception:
        pass

    return response


async def update_fvg_entry(
    *,
    fvg_id: str,
    verb: str | None = None,
    phrase: str | None = None,
    noun: str | None = None,
    prep: str | None = None,
    structure_type: str | None = None,
    semantic_type: str | None = None,
) -> dict[str, str]:
    response = correct_fvg_entry(
        fvg_id=fvg_id,
        verb=verb,
        phrase=phrase,
        noun=noun,
        prep=prep,
        structure_type=structure_type,
        semantic_type=semantic_type,
    )

    try:
        await publish(FVG_UPDATED, response)
    except Exception:
        pass

    return response
