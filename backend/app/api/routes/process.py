from fastapi import APIRouter, HTTPException

from app.schemas.processings import (
    ImportRuleProcessRequest,
    LemmatizeProcessRequest,
    ProcessingItem,
    SentenceSegmentationProcessRequest,
)
from app.schemas.sentences import SentenceSegmentationResponse
from app.services.process.process_query_service import list_processing_items
from app.services.process.rule.main import import_rule as import_rule_process
from app.services.process.sentence_lemmatization import lemmatize_sentences
from app.services.process.sentence_segmentation import segment_document_sentences

router = APIRouter()


@router.get("/process", response_model=list[ProcessingItem])
def get_processes_route() -> list[ProcessingItem]:
    try:
        return list_processing_items()
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/process/sentence_segmentation", response_model=SentenceSegmentationResponse)
def segment_document_sentences_route(
    payload: SentenceSegmentationProcessRequest,
) -> SentenceSegmentationResponse:
    try:
        return segment_document_sentences(payload.doc_id, payload.preview_length)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/process/lemmatize", response_model=ProcessingItem)
def lemmatize_sentences_route(payload: LemmatizeProcessRequest) -> ProcessingItem:
    try:
        return lemmatize_sentences(segmentation_id=payload.segmentation_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/process/import_rule")
def import_rule_route(payload: ImportRuleProcessRequest) -> dict[str, object]:
    try:
        return import_rule_process(
            {
                "path": payload.path,
                "type": payload.type,
            }
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error
