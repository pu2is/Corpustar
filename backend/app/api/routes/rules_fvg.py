from fastapi import APIRouter, HTTPException

from app.core.log import get_logger, log_event
from app.schemas.rules import (
    AddFvgRuleRequest,
    FvgRuleItem,
    RemoveFvgRuleResponse,
    UpdateFvgRuleRequest,
)
from app.services.rules.fvg.modify_rule import add_fvg_rule, modify_fvg_rule, remove_fvg_rule
from app.services.rules.fvg.rule_query import list_fvg_rules
from app.socket.socket_events import FVG_RULE_APPENDED, FVG_RULE_REMOVED, FVG_RULE_UPDATED
from app.socket.socket_publisher import publish

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


@router.get("/rules/fvg/{rule_id}", response_model=list[FvgRuleItem])
def list_fvg_rules_route(rule_id: str) -> list[FvgRuleItem]:
    function_name = "list_fvg_rules_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        rule_id=rule_id,
    )

    try:
        response = list_fvg_rules(rule_id=rule_id)
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=rule_id,
            result=len(response),
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
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=rule_id,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
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


@router.post("/rules/add-fvg", response_model=FvgRuleItem)
async def add_fvg_rule_route(payload: AddFvgRuleRequest) -> FvgRuleItem:
    function_name = "add_fvg_rule_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        rule_id=payload.ruleId,
    )

    try:
        response = add_fvg_rule(
            rule_id=payload.ruleId,
            verb=payload.verb,
            phrase=payload.phrase,
        )

        try:
            await publish(FVG_RULE_APPENDED, response)
        except Exception as broadcast_error:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                rule_id=payload.ruleId,
                error=f"Broadcast failed: {broadcast_error}",
                exc_info=True,
            )

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=payload.ruleId,
            result=response["id"],
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=payload.ruleId,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=payload.ruleId,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            rule_id=payload.ruleId,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.delete("/rules/rm-fvg/{fvg_rule_id}", response_model=RemoveFvgRuleResponse)
async def remove_fvg_rule_route(fvg_rule_id: str) -> RemoveFvgRuleResponse:
    function_name = "remove_fvg_rule_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        fvg_rule_id=fvg_rule_id,
    )

    try:
        response = remove_fvg_rule(fvg_rule_id=fvg_rule_id)

        try:
            await publish(FVG_RULE_REMOVED, response)
        except Exception as broadcast_error:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                fvg_rule_id=fvg_rule_id,
                error=f"Broadcast failed: {broadcast_error}",
                exc_info=True,
            )

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            fvg_rule_id=fvg_rule_id,
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            fvg_rule_id=fvg_rule_id,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            fvg_rule_id=fvg_rule_id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.patch("/rules/fvg/{fvg_rule_id}", response_model=FvgRuleItem)
async def modify_fvg_rule_route(fvg_rule_id: str, payload: UpdateFvgRuleRequest,) -> FvgRuleItem:
    function_name = "modify_fvg_rule_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        fvg_rule_id=fvg_rule_id,
    )

    try:
        response = modify_fvg_rule(
            fvg_rule_id=fvg_rule_id,
            verb=payload.verb,
            phrase=payload.phrase,
        )

        try:
            await publish(FVG_RULE_UPDATED, response)
        except Exception as broadcast_error:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                fvg_rule_id=fvg_rule_id,
                error=f"Broadcast failed: {broadcast_error}",
                exc_info=True,
            )

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            fvg_rule_id=fvg_rule_id,
            result=response["id"],
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            fvg_rule_id=fvg_rule_id,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            fvg_rule_id=fvg_rule_id,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            fvg_rule_id=fvg_rule_id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error
