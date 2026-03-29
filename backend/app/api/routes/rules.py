from fastapi import APIRouter, HTTPException

from app.schemas.rules import RemoveRuleResponse, RuleItem
from app.services.rules.rule_query import get_all_rules, get_rule
from app.services.rules.rule_remove import remove_rule
from app.socket.socket_events import RULE_ITEM_REMOVED
from app.socket.socket_publisher import publish

router = APIRouter()


@router.get("/rule", response_model=list[RuleItem])
def get_all_rules_route() -> list[RuleItem]:
    try:
        return get_all_rules()
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.delete("/rule/{rule_id}", response_model=RemoveRuleResponse)
async def remove_rule_route(rule_id: str) -> RemoveRuleResponse:
    try:
        existing = get_rule(rule_id)
        if existing is None:
            raise FileNotFoundError(f"Rule not found: {rule_id}")

        response = remove_rule(rule_id=rule_id)

        try:
            await publish(RULE_ITEM_REMOVED, existing)
        except Exception:
            pass

        return {"id": str(response["id"])}
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error
