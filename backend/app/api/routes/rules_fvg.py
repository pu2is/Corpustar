from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.process.fvg_entries.api import (
    append_fvg_entry,
    delete_fvg_entry,
    list_fvg_entry_items,
    update_fvg_entry,
)
from app.schemas.rules import (
    AppendFvgEntryRequest,
    CorrectFvgEntryRequest,
    FvgActionResponse,
    FvgEntryItem,
)

router = APIRouter()


@router.get("/fvg/{rule_id}", response_model=list[FvgEntryItem])
def list_fvg_rules_route(rule_id: str) -> list[FvgEntryItem]:
    try:
        return list_fvg_entry_items(rule_id=rule_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/fvg/append", response_model=FvgActionResponse)
async def add_fvg_rule_route(payload: AppendFvgEntryRequest) -> FvgActionResponse | JSONResponse:
    try:
        item = await append_fvg_entry(
            rule_id=payload.rule_id,
            verb=payload.verb,
            phrase=payload.phrase,
            noun=payload.noun,
            prep=payload.prep,
            structure_type=payload.structure_type,
            semantic_type=payload.semantic_type,
        )
        return {"id": item["id"], "ok": True, "error_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": "", "ok": False, "error_msg": str(error)},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"id": "", "ok": False, "error_msg": str(error)},
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"id": "", "ok": False, "error_msg": "Internal server error"},
        )


@router.delete("/fvg/{fvg_id}", response_model=FvgActionResponse)
async def remove_fvg_rule_route(fvg_id: str) -> FvgActionResponse | JSONResponse:
    try:
        response = await delete_fvg_entry(fvg_id=fvg_id)
        return {"id": str(response["id"]), "ok": True, "error_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": fvg_id, "ok": False, "error_msg": str(error)},
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"id": fvg_id, "ok": False, "error_msg": "Internal server error"},
        )


@router.post("/fvg/correct", response_model=FvgActionResponse)
async def modify_fvg_rule_route(payload: CorrectFvgEntryRequest) -> FvgActionResponse | JSONResponse:
    try:
        item = await update_fvg_entry(
            fvg_id=payload.id,
            verb=payload.verb,
            phrase=payload.phrase,
            noun=payload.noun,
            prep=payload.prep,
            structure_type=payload.structure_type,
            semantic_type=payload.semantic_type,
        )
        return {"id": item["id"], "ok": True, "error_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": payload.id, "ok": False, "error_msg": str(error)},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"id": payload.id, "ok": False, "error_msg": str(error)},
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"id": payload.id, "ok": False, "error_msg": "Internal server error"},
        )
