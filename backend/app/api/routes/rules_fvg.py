from fastapi import APIRouter, HTTPException

from app.core.process.fvg_entries.api import (
    append_fvg_entry,
    delete_fvg_entry,
    list_fvg_entry_items,
    update_fvg_entry,
)
from app.schemas.rules import (
    AppendFvgEntryRequest,
    CorrectFvgEntryRequest,
    FvgEntryItem,
    RemoveFvgEntryResponse,
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


@router.post("/fvg/append", response_model=FvgEntryItem)
async def add_fvg_rule_route(payload: AppendFvgEntryRequest) -> FvgEntryItem:
    try:
        return await append_fvg_entry(
            rule_id=payload.rule_id,
            verb=payload.verb,
            phrase=payload.phrase,
            noun=payload.noun,
            prep=payload.prep,
            structure_type=payload.structure_type,
            semantic_type=payload.semantic_type,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.delete("/fvg/{fvg_id}", response_model=RemoveFvgEntryResponse)
async def remove_fvg_rule_route(fvg_id: str) -> RemoveFvgEntryResponse:
    try:
        return await delete_fvg_entry(fvg_id=fvg_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/fvg/correct", response_model=FvgEntryItem)
async def modify_fvg_rule_route(payload: CorrectFvgEntryRequest) -> FvgEntryItem:
    try:
        return await update_fvg_entry(
            fvg_id=payload.id,
            verb=payload.verb,
            phrase=payload.phrase,
            noun=payload.noun,
            prep=payload.prep,
            structure_type=payload.structure_type,
            semantic_type=payload.semantic_type,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error
