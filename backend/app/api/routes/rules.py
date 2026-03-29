from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.rules import RuleActionResponse, RuleItem
from app.services.rules.rule_query import get_all_rules, get_rule
from app.services.rules.rule_remove import remove_rule
from app.socket.socket_events import RULE_REMOVED
from app.socket.socket_publisher import publish

router = APIRouter()


@router.get("/rule", response_model=list[RuleItem])
def get_all_rules_route() -> list[RuleItem]:
    try:
        return get_all_rules()
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


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
            await publish(RULE_REMOVED, existing)
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
