from fastapi import APIRouter, HTTPException

from app.schemas.fvg_candidates import (
    SentenceFvgDetectedListRequest,
    SentenceFvgListItem,
    SentenceFvgListRequest,
)
from app.services.fvg_candidates.load import (
    collect_detected_fvg_candidates_by_cursor,
    collect_fvg_candidates_and_sentence_by_cursor,
    collect_undetected_fvg_candidates_by_cursor,
)

router = APIRouter()


@router.post("/fvg_candidates", response_model=SentenceFvgListItem)
def get_fvg_candidates_by_cursor(payload: SentenceFvgListRequest) -> SentenceFvgListItem:
    try:
        return collect_fvg_candidates_and_sentence_by_cursor(
            segmentation_id=payload.segmentation_id,
            cursor=payload.cursor,
            limit=payload.limit,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/fvg_candidates/detected", response_model=SentenceFvgListItem)
def get_detected_fvg_candidates_by_cursor(
    payload: SentenceFvgDetectedListRequest,
) -> SentenceFvgListItem:
    try:
        return collect_detected_fvg_candidates_by_cursor(
            fvg_process_id=payload.fvg_process_id,
            cursor=payload.cursor,
            limit=payload.limit,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/fvg_candidates/undetected", response_model=SentenceFvgListItem)
def get_undetected_fvg_candidates_by_cursor(
    payload: SentenceFvgDetectedListRequest,
) -> SentenceFvgListItem:
    try:
        return collect_undetected_fvg_candidates_by_cursor(
            fvg_process_id=payload.fvg_process_id,
            cursor=payload.cursor,
            limit=payload.limit,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error
