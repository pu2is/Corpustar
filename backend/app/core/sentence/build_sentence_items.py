from app.services.sentence.types import SentenceItem, SentenceRow


def validate_sentence_offsets(
    sentence_id: str,
    start_offset: int,
    end_offset: int,
    full_text_length: int,
) -> None:
    if start_offset < 0:
        raise ValueError(f"Sentence {sentence_id} has negative start offset: {start_offset}")
    if end_offset <= start_offset:
        raise ValueError(
            f"Sentence {sentence_id} has invalid offsets: start={start_offset}, end={end_offset}"
        )
    if end_offset > full_text_length:
        raise ValueError(
            f"Sentence {sentence_id} offset out of range: end={end_offset}, text_length={full_text_length}"
        )


def build_sentence_item(
    sentence_id: str,
    doc_id: str,
    processing_id: str,
    start_offset: int,
    end_offset: int,
    lemma_text: str | None,
    full_text: str,
    source_text: str | None = None,
) -> SentenceItem:
    validate_sentence_offsets(
        sentence_id=sentence_id,
        start_offset=start_offset,
        end_offset=end_offset,
        full_text_length=len(full_text),
    )

    return {
        "id": sentence_id,
        "docId": doc_id,
        "processingId": processing_id,
        "startOffset": start_offset,
        "endOffset": end_offset,
        "text": source_text if source_text is not None else full_text[start_offset:end_offset],
        "lemmaText": lemma_text,
    }


def build_sentence_item_from_row(sentence_row: SentenceRow, full_text: str) -> SentenceItem:
    lemma_text = sentence_row.get("lemma_text")
    source_text = sentence_row.get("source_text")
    return build_sentence_item(
        sentence_id=str(sentence_row["id"]),
        doc_id=str(sentence_row["doc_id"]),
        processing_id=str(sentence_row["processing_id"]),
        start_offset=int(sentence_row["start_offset"]),
        end_offset=int(sentence_row["end_offset"]),
        lemma_text=str(lemma_text) if lemma_text is not None else None,
        full_text=full_text,
        source_text=str(source_text) if source_text is not None else None,
    )
