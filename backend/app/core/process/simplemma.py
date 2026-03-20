from collections.abc import Iterable, Iterator, Sequence
from typing import TypeVar

try:
    from simplemma import text_lemmatizer
except ImportError:
    text_lemmatizer = None


GERMAN_LANGUAGE = "de"
GERMAN_GREEDY_LEMMA = True
SENTENCE_BATCH_SIZE = 256
T = TypeVar("T")
SentenceRow = dict[str, int | str | None]
LemmaRow = dict[str, str | None]


def iter_sentence_batches(items: Iterable[T], batch_size: int = SENTENCE_BATCH_SIZE) -> Iterator[list[T]]:
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def lemmatize_german_text(source_text: str) -> str:
    if text_lemmatizer is None:
        raise RuntimeError("simplemma is required for sentence lemmatization.")

    if not source_text:
        return ""

    lemma_tokens = text_lemmatizer(
        source_text,
        lang=GERMAN_LANGUAGE,
        greedy=GERMAN_GREEDY_LEMMA,
    )
    normalized_tokens = [
        token.lower()
        for token in lemma_tokens
        if any(character.isalnum() for character in token)
    ]
    return " ".join(normalized_tokens)


def build_lemma_row(sentence_row: SentenceRow, lemma_text: str) -> LemmaRow:
    sentence_id = str(sentence_row["id"])
    start_offset = int(sentence_row["start_offset"])
    return {
        "id": f"{sentence_id}_{start_offset}",
        "doc_id": str(sentence_row["doc_id"]),
        "segmentation_id": str(sentence_row["processing_id"]),
        "sentence_id": sentence_id,
        "source_text": str(sentence_row["source_text"] or ""),
        "lemma_text": lemma_text,
        "corrected_lemma": lemma_text,
        "fvg_result_id": None,
    }


def build_lemma_rows(sentence_rows: Sequence[SentenceRow], lemma_texts: Sequence[str]) -> list[LemmaRow]:
    if not sentence_rows:
        return []

    return [
        build_lemma_row(sentence_row=sentence_row, lemma_text=lemma_text)
        for sentence_row, lemma_text in zip(sentence_rows, lemma_texts, strict=True)
    ]
