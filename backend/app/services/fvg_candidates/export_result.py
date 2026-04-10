import csv
import os
from collections import defaultdict

from app.core.log import get_logger, log_event
from app.infrastructure.repositories.fvg_candidates import get_fvg_candidate_items_by_process_id
from app.infrastructure.repositories.fvg_entries import get_fvg_entry_by_id
from app.infrastructure.repositories.lemma_tokens import read_lemma_tokens_by_sentence_ids
from app.infrastructure.repositories.sentences import get_sentences_by_ids

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def get_fvg_result(process_id: str, path: str, filename: str) -> str:
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE, function_name="get_fvg_result", process_id=process_id)

    candidates = get_fvg_candidate_items_by_process_id(process_id)

    # count occurrences per fvg entry
    entry_counts: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        entry_counts[str(candidate["algo_fvg_entry_id"])] += 1

    # batch-fetch sentences and lemma tokens
    sentence_ids = list({str(c["sentence_id"]) for c in candidates})
    sentences_by_id = {str(row["id"]): row for row in get_sentences_by_ids(sentence_ids)}
    lemma_tokens_by_sentence_id = read_lemma_tokens_by_sentence_ids(sentence_ids)

    # cache fvg entries to avoid redundant DB lookups
    fvg_entry_cache: dict[str, object] = {}

    def _get_entry(entry_id: str) -> object:
        if entry_id not in fvg_entry_cache:
            fvg_entry_cache[entry_id] = get_fvg_entry_by_id(entry_id)
        return fvg_entry_cache[entry_id]

    sorted_candidates = sorted(candidates, key=lambda c: str(c["algo_fvg_entry_id"]))

    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, filename)

    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(["fvg_verb", "fvg_phrase", "count", "matched_verb", "matched_phrase", "sentence", "lemma"])

        for candidate in sorted_candidates:
            entry_id = str(candidate["algo_fvg_entry_id"])
            entry = _get_entry(entry_id)

            fvg_verb = str(entry["verb"]) if entry else ""
            fvg_phrase = str(entry["phrase"]) if entry else ""
            count = entry_counts[entry_id]

            matched_verb = str(candidate["algo_verb_token"])
            prep_token = str(candidate["algo_prep_token"])
            noun_token = str(candidate["algo_noun_token"])
            matched_phrase = f"{prep_token} {noun_token}".strip() if prep_token else noun_token

            sentence_id = str(candidate["sentence_id"])
            sentence_row = sentences_by_id.get(sentence_id)
            sentence_text = str(sentence_row["corrected_text"]) if sentence_row else ""

            lemma_tokens = lemma_tokens_by_sentence_id.get(sentence_id, [])
            sorted_lemma = sorted(lemma_tokens, key=lambda t: int(t["word_index"]))
            lemma_text = " ".join(str(t["lemma_word"]) for t in sorted_lemma)

            writer.writerow([fvg_verb, fvg_phrase, count, matched_verb, matched_phrase, sentence_text, lemma_text])

    log_event(LOGGER, stage="OK", module_file=MODULE_FILE, function_name="get_fvg_result", file_path=file_path)
    return file_path
