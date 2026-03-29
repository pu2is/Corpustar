from collections.abc import Iterable, Iterator, Sequence

from app.core.process.lemmatize import lemmatize_sentence_to_tokens


SENTENCE_BATCH_SIZE = 256


def iter_sentence_batches(items: Iterable[dict[str, object]], batch_size: int = SENTENCE_BATCH_SIZE) -> Iterator[list[dict[str, object]]]:
    batch: list[dict[str, object]] = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def build_lemma_rows(sentence_rows: Sequence[dict[str, object]], version_id: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sentence_row in sentence_rows:
        rows.extend(lemmatize_sentence_to_tokens(sentence_row, version_id=version_id))
    return rows
