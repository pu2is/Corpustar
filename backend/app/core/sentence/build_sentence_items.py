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
    *,
    sentence_id: str,
    version_id: str,
    doc_id: str,
    start_offset: int,
    end_offset: int,
    source_text: str,
    corrected_text: str,
    full_text: str | None = None,
) -> SentenceItem:
    if full_text is not None:
        validate_sentence_offsets(
            sentence_id=sentence_id,
            start_offset=start_offset,
            end_offset=end_offset,
            full_text_length=len(full_text),
        )

    return {
        "id": sentence_id,
        "version_id": version_id,
        "doc_id": doc_id,
        "start_offset": start_offset,
        "end_offset": end_offset,
        "source_text": source_text,
        "corrected_text": corrected_text,
    }


def build_sentence_item_from_row(sentence_row: SentenceRow, full_text: str | None = None) -> SentenceItem:
    return build_sentence_item(
        sentence_id=str(sentence_row["id"]),
        version_id=str(sentence_row["version_id"]),
        doc_id=str(sentence_row["doc_id"]),
        start_offset=int(sentence_row["start_offset"]),
        end_offset=int(sentence_row["end_offset"]),
        source_text=str(sentence_row["source_text"]),
        corrected_text=str(sentence_row["corrected_text"]),
        full_text=full_text,
    )
