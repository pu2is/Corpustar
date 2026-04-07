from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.processings import (
    FvgCandidateProcessActionResponse,
    FvgCandidateProcessRequest,
    ImportRuleActionResponse,
    ImportRuleProcessRequest,
    LemmatizeProcessRequest,
    ProcessActionResponse,
    ProcessingItem,
    SentenceSegmentationProcessRequest,
)
from app.services.process.process_query_service import list_processing_items
from app.services.process.remove import remove_results_by_fvg_process_id
from app.services.process.rule.main import import_rule as import_rule_process
from app.services.process.fvg_candidates import run_fvg_candidate_matching
from app.services.process.sentence_lemmatization import lemmatize_sentences
from app.services.process.sentence_segmentation import segment_document_sentences

router = APIRouter()


@router.get("/process", response_model=list[ProcessingItem])
def get_processes_route() -> list[ProcessingItem]:
    try:
        return list_processing_items()
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/process/sentence_segmentation", response_model=ProcessActionResponse)
def segment_document_sentences_route(
    payload: SentenceSegmentationProcessRequest,
) -> ProcessActionResponse | JSONResponse:
    try:
        process_item = segment_document_sentences(payload.doc_id, payload.preview_length)
        return {"id": process_item["id"], "ok": True, "error_msg": ""}
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


@router.post("/process/lemmatize", response_model=ProcessActionResponse)
def lemmatize_sentences_route(payload: LemmatizeProcessRequest) -> ProcessActionResponse | JSONResponse:
    try:
        process_item = lemmatize_sentences(segmentation_id=payload.segmentation_id)
        return {"id": process_item["id"], "ok": True, "error_msg": ""}
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


@router.post("/process/import_rule", response_model=ImportRuleActionResponse)
def import_rule_route(payload: ImportRuleProcessRequest) -> ImportRuleActionResponse | JSONResponse:
    try:
        import_rule_process(
            {
                "path": payload.path,
                "type": payload.type,
            }
        )
        return {"ok": True, "error_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"ok": False, "error_msg": str(error)},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error_msg": str(error)},
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error_msg": "Internal server error"},
        )


@router.post("/process/fvg_candidate", response_model=FvgCandidateProcessActionResponse)
def fvg_candidate_route(
    payload: FvgCandidateProcessRequest,
) -> FvgCandidateProcessActionResponse | JSONResponse:
    try:
        process_item = run_fvg_candidate_matching(
            segmentation_id=payload.segmentation_id,
            rule_id=payload.rule_id,
        )
        return {
            "id": process_item["id"],
            "state": process_item["state"],
            "error_msg": "",
        }
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": "", "state": "failed", "error_msg": str(error)},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"id": "", "state": "failed", "error_msg": str(error)},
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"id": "", "state": "failed", "error_msg": "Internal server error"},
        )


@router.delete("/process/fvg_candidate/{process_id}", response_model=None)
def delete_fvg_candidate_results_route(process_id: str) -> dict[str, object] | JSONResponse:
    try:
        remove_results_by_fvg_process_id(process_id)
        return {"ok": True, "err_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"ok": False, "err_msg": str(error)},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "err_msg": str(error)},
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "err_msg": "Internal server error"},
        )
