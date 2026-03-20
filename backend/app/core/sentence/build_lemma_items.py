from collections.abc import Mapping


LemmaRow = Mapping[str, str | None]
LemmaItem = dict[str, str | None]


def build_lemma_item(
    lemma_id: str,
    doc_id: str,
    segmentation_id: str,
    sentence_id: str,
    source_text: str,
    lemma_text: str,
    corrected_lemma: str,
    fvg_result_id: str | None = None,
) -> LemmaItem:
    return {
        "id": lemma_id,
        "docId": doc_id,
        "segmentationId": segmentation_id,
        "sentenceId": sentence_id,
        "sourceText": source_text,
        "lemmaText": lemma_text,
        "correctedLemma": corrected_lemma,
        "fvgResultId": fvg_result_id,
    }


def build_lemma_item_from_row(lemma_row: LemmaRow) -> LemmaItem:
    return build_lemma_item(
        lemma_id=str(lemma_row["id"]),
        doc_id=str(lemma_row["doc_id"]),
        segmentation_id=str(lemma_row["segmentation_id"]),
        sentence_id=str(lemma_row["sentence_id"]),
        source_text=str(lemma_row["source_text"] or ""),
        lemma_text=str(lemma_row["lemma_text"] or ""),
        corrected_lemma=str(lemma_row["corrected_lemma"] or ""),
        fvg_result_id=str(lemma_row["fvg_result_id"]) if lemma_row["fvg_result_id"] is not None else None,
    )
