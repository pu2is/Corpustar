from fastapi import APIRouter, HTTPException

from app.core.log import get_logger, log_event
from app.schemas.rules import ImportRuleRequest, RemoveRuleResponse, RuleItem
from app.services.rules.import_rule import import_rule
from app.services.rules.rule_query import get_all_rules, get_rule
from app.services.rules.rule_remove import remove_rule
from app.socket.socket_events import (
    FVG_RULES_CREATED,
    FVG_RULES_REMOVED,
    RULE_CREATED,
    RULE_REMOVED,
)
from app.socket.socket_publisher import publish

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


@router.get("/rules", response_model=list[RuleItem])
def get_all_rules_route() -> list[RuleItem]:
    function_name = "get_all_rules_route"
    log_event(LOGGER, stage="CALL",
        module_file=MODULE_FILE, function_name=function_name)

    try:
        rules = get_all_rules()
        log_event(LOGGER, stage="OK", module_file=MODULE_FILE,
            function_name=function_name, result=len(rules))
        return rules
    except Exception as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, error=str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.get("/rules/{rule_id}", response_model=RuleItem | None)
def get_rule_route(rule_id: str) -> RuleItem | None:
    function_name = "get_rule_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        rule_id=rule_id,
    )

    try:
        rule = get_rule(rule_id=rule_id)
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=rule_id,
            result="found" if rule is not None else "not_found",
        )
        return rule
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
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/rules", response_model=RuleItem)
async def import_rule_route(payload: ImportRuleRequest) -> RuleItem:
    function_name = "import_rule_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        rule_type=payload.type,
    )

    try:
        import_result = import_rule(path=payload.path, rule_type=payload.type)
        rule_item = import_result["rule"]

        try:
            await publish(RULE_CREATED, rule_item)
            await publish(
                FVG_RULES_CREATED,
                {
                    "ruleId": rule_item["id"],
                    "count": import_result["importedCount"],
                },
            )
        except Exception as broadcast_error:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                error=f"Broadcast failed: {broadcast_error}",
                exc_info=True,
            )

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=rule_item["id"],
            imported_count=import_result["importedCount"],
        )
        return rule_item
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.delete("/rules/{rule_id}", response_model=RemoveRuleResponse)
async def remove_rule_route(rule_id: str) -> RemoveRuleResponse:
    function_name = "remove_rule_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        rule_id=rule_id,
    )

    try:
        response = remove_rule(rule_id=rule_id)

        try:
            await publish(RULE_REMOVED, {"id": rule_id})
            await publish(
                FVG_RULES_REMOVED,
                {
                    "ruleId": rule_id,
                    "count": response["removedFvgCount"],
                },
            )
        except Exception as broadcast_error:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                rule_id=rule_id,
                error=f"Broadcast failed: {broadcast_error}",
                exc_info=True,
            )

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=rule_id,
            removed_fvg_count=response["removedFvgCount"],
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=rule_id,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
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
        raise HTTPException(status_code=500, detail="Internal server error") from error
