from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.fvg_candidates import (
    FvgCandidateAddRequest,
    FvgCandidateToggleRequest,
    FvgCandidateToggleResponse,
    FvgExportRequest,
    SentenceFvgDetectedListRequest,
    SentenceFvgListItem,
    SentenceFvgListRequest,
)
from app.services.fvg_candidates.edit import add_fvg_candidate, remove_fvg_candidate, restore_fvg_candidate
from app.services.fvg_candidates.export_result import get_fvg_result
from app.services.fvg_candidates.load import (
    collect_detected_fvg_candidates_by_cursor,
    collect_fvg_candidates_and_sentence_by_cursor,
    collect_undetected_fvg_candidates_by_cursor,
)
from app.services.fvg_candidates.statistics import get_simple_statistics

router = APIRouter()


@router.get("/fvg_candidates/statistics/{process_id}")
def get_fvg_statistics_route(process_id: str) -> dict[str, int]:
    try:
        return get_simple_statistics(fvg_process_id=process_id)
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
            verb_filter=payload.verb_filter,
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
            verb_filter=payload.verb_filter,
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
            verb_filter=payload.verb_filter,
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


@router.post("/fvg_candidates/add", response_model=FvgCandidateToggleResponse)
def add_fvg_candidate_route(payload: FvgCandidateAddRequest) -> FvgCandidateToggleResponse:
    try:
        return add_fvg_candidate(
            sentence_id=payload.sentence_id,
            process_id=payload.process_id,
            fvg_entry_id=payload.fvg_entry_id,
            verb_id=payload.verb_id,
            noun_id=payload.noun_id,
            prep_id=payload.prep_id,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/fvg_candidates/export_result/{process_id}")
def export_fvg_result_route(process_id: str, payload: FvgExportRequest) -> FileResponse:
    try:
        file_path = get_fvg_result(process_id=process_id, path=payload.path, filename=payload.filename)
        return FileResponse(path=file_path, media_type="text/csv", filename=payload.filename)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error
