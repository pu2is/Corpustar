from fastapi import APIRouter, HTTPException

from app.schemas.fvg_candidates import (
    FvgCandidateToggleRequest,
    FvgCandidateToggleResponse,
    SentenceFvgDetectedListRequest,
    SentenceFvgListItem,
    SentenceFvgListRequest,
)
from app.services.fvg_candidates.edit import remove_fvg_candidate, restore_fvg_candidate
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


@router.post("/fvg_candidates/remove", response_model=FvgCandidateToggleResponse)
def remove_fvg_candidate_route(payload: FvgCandidateToggleRequest) -> FvgCandidateToggleResponse:
    try:
        return remove_fvg_candidate(
            fvg_candidate_id=payload.fvg_candidate_id,
            sentence_id=payload.sentence_id,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/fvg_candidates/restore", response_model=FvgCandidateToggleResponse)
def restore_fvg_candidate_route(payload: FvgCandidateToggleRequest) -> FvgCandidateToggleResponse:
    try:
        return restore_fvg_candidate(
            fvg_candidate_id=payload.fvg_candidate_id,
            sentence_id=payload.sentence_id,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error



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
