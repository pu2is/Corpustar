from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.rules import RuleActionResponse, RuleCloneResponse, RuleItem
from app.services.rules.clone import do_clone_rule
from app.services.rules.rule_query import get_all_rules, get_rule
from app.services.rules.rule_remove import remove_rule
from app.socket.socket_events import RULE_COPY_FINISHED, RULE_REMOVED
from app.socket.socket_publisher import publish

router = APIRouter()


@router.get("/rule", response_model=list[RuleItem])
def get_all_rules_route() -> list[RuleItem]:
    try:
        return get_all_rules()
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/rule/clone/{rule_id}", response_model=RuleCloneResponse)
async def clone_rule_dict(rule_id: str) -> RuleCloneResponse | JSONResponse:
    try:
        cloned_rule = do_clone_rule(rule_id)

        rule_item = RuleItem(
            id=cloned_rule["id"],
            version_id=cloned_rule["version_id"],
            type=cloned_rule["type"],
            path=cloned_rule["path"],
        )

        try:
            await publish(RULE_COPY_FINISHED, {"ok": True, "err_msg": "", "item": rule_item})
        except Exception:
            pass

        return {"ok": True, "err_msg": ""}
    except FileNotFoundError as error:
        try:
            await publish(RULE_COPY_FINISHED, {"ok": False, "err_msg": str(error), "item": None})
        except Exception:
            pass

        return JSONResponse(
            status_code=404,
            content={"ok": False, "err_msg": str(error)},
        )
    except Exception as error:
        try:
            await publish(RULE_COPY_FINISHED, {"ok": False, "err_msg": "Internal server error", "item": None})
        except Exception:
            pass

        return JSONResponse(
            status_code=500,
            content={"ok": False, "err_msg": "Internal server error"},
        )


@router.delete("/rule/{rule_id}", response_model=RuleActionResponse)
async def remove_rule_route(rule_id: str) -> RuleActionResponse | JSONResponse:
    try:
        existing = get_rule(rule_id)
        if existing is None:
            return JSONResponse(
                status_code=404,
                content={"id": rule_id, "ok": False, "err_msg": f"Rule not found: {rule_id}"},
            )

        response = remove_rule(rule_id=rule_id)

        try:
            await publish(RULE_REMOVED, {"id": str(response["id"])})
        except Exception:
            pass

        return {"id": str(response["id"]), "ok": True, "err_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": rule_id, "ok": False, "err_msg": str(error)},
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"id": rule_id, "ok": False, "err_msg": "Internal server error"},
        )
