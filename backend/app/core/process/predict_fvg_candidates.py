from collections import defaultdict
from collections.abc import Mapping, Sequence
from uuid import uuid4

LemmaToken = Mapping[str, int | str]
FvgEntry = Mapping[str, str]
FvgCandidate = dict[str, int | str | bool]


def _to_str(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _to_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def _build_candidate(
    *,
    sentence_id: str,
    fvg_entry_id: str,
    verb_token: LemmaToken,
    noun_token: LemmaToken,
    prep_token: LemmaToken | None,
) -> FvgCandidate:
    prep_word = _to_str(prep_token["lemma_word"]) if prep_token is not None else ""
    prep_index = _to_int(prep_token["word_index"], -1) if prep_token is not None else -1

    return {
        "id": str(uuid4()),
        "sentence_id": sentence_id,
        "algo_fvg_entry_id": fvg_entry_id,
        "corrected_fvg_entry_id": fvg_entry_id,
        "algo_verb_token": _to_str(verb_token["lemma_word"]),
        "algo_verb_index": _to_int(verb_token["word_index"]),
        "corrected_verb_token": _to_str(verb_token["lemma_word"]),
        "corrected_verb_index": _to_int(verb_token["word_index"]),
        "algo_noun_token": _to_str(noun_token["lemma_word"]),
        "algo_noun_index": _to_int(noun_token["word_index"]),
        "corrected_noun_token": _to_str(noun_token["lemma_word"]),
        "corrected_noun_index": _to_int(noun_token["word_index"]),
        "algo_prep_token": prep_word,
        "algo_prep_index": prep_index,
        "corrected_prep_token": prep_word,
        "corrected_prep_index": prep_index,
        "label": "",
        "manuelle_created": False,
        "removed": False,
    }


def predict_fvg_candidates(
    fvg_entries: Sequence[FvgEntry],
    lemma_tokens: Sequence[LemmaToken],
) -> list[FvgCandidate]:
    if not fvg_entries or not lemma_tokens:
        return []

    entries_by_verb: dict[str, list[FvgEntry]] = defaultdict(list)
    for entry in fvg_entries:
        entries_by_verb[_to_str(entry.get("verb", "")).lower()].append(entry)

    lemma_by_sentence_id: dict[str, list[LemmaToken]] = defaultdict(list)
    for token in lemma_tokens:
        lemma_by_sentence_id[_to_str(token.get("sentence_id", ""))].append(token)

    candidates: list[FvgCandidate] = []
    for sentence_id, sentence_tokens in lemma_by_sentence_id.items():
        ordered_tokens = sorted(sentence_tokens, key=lambda token: _to_int(token.get("word_index"), 0))

        for verb_token in ordered_tokens:
            if _to_str(verb_token.get("pos_tag", "")).upper() != "VERB":
                continue

            verb_lemma = _to_str(verb_token.get("lemma_word", "")).lower()
            verb_entries = entries_by_verb.get(verb_lemma)
            if not verb_entries:
                continue

            verb_index = _to_int(verb_token.get("word_index"), -1)
            child_tokens = [
                token for token in ordered_tokens if _to_int(token.get("head_index"), -999999) == verb_index
            ]

            matched_candidate = _find_akku_candidate(sentence_id, verb_token, child_tokens, verb_entries)
            if matched_candidate is not None:
                candidates.append(matched_candidate)
                continue

            matched_prep_candidate = _find_prep_candidate(
                sentence_id=sentence_id,
                verb_token=verb_token,
                child_tokens=child_tokens,
                all_tokens=ordered_tokens,
                verb_entries=verb_entries,
            )
            if matched_prep_candidate is not None:
                candidates.append(matched_prep_candidate)

    return candidates


def _find_akku_candidate(
    sentence_id: str,
    verb_token: LemmaToken,
    child_tokens: Sequence[LemmaToken],
    verb_entries: Sequence[FvgEntry],
) -> FvgCandidate | None:
    akku_entries_by_noun = {
        _to_str(entry.get("noun", "")).lower(): entry
        for entry in verb_entries
        if _to_str(entry.get("structure_type", "")).lower() == "akku"
    }
    if not akku_entries_by_noun:
        return None

    for child in child_tokens:
        if _to_str(child.get("pos_tag", "")).upper() != "NOUN":
            continue

        noun_lemma = _to_str(child.get("lemma_word", "")).lower()
        matched_entry = akku_entries_by_noun.get(noun_lemma)
        if matched_entry is None:
            continue

        return _build_candidate(
            sentence_id=sentence_id,
            fvg_entry_id=_to_str(matched_entry.get("id")),
            verb_token=verb_token,
            noun_token=child,
            prep_token=None,
        )

    return None


def _find_prep_candidate(
    *,
    sentence_id: str,
    verb_token: LemmaToken,
    child_tokens: Sequence[LemmaToken],
    all_tokens: Sequence[LemmaToken],
    verb_entries: Sequence[FvgEntry],
) -> FvgCandidate | None:
    prep_entries: list[FvgEntry] = [
        entry
        for entry in verb_entries
        if _to_str(entry.get("structure_type", "")).lower() == "prep"
    ]
    if not prep_entries:
        return None

    entries_by_prep: dict[str, list[FvgEntry]] = defaultdict(list)
    for entry in prep_entries:
        entries_by_prep[_to_str(entry.get("prep", "")).lower()].append(entry)

    for prep_token in child_tokens:
        if _to_str(prep_token.get("pos_tag", "")).upper() != "ADP":
            continue

        prep_word = _to_str(prep_token.get("lemma_word", "")).lower()
        prep_matched_entries = entries_by_prep.get(prep_word)
        if not prep_matched_entries:
            continue

        prep_index = _to_int(prep_token.get("word_index"), -1)
        grand_children = [
            token for token in all_tokens if _to_int(token.get("head_index"), -999999) == prep_index
        ]
        noun_entry_map = {
            _to_str(entry.get("noun", "")).lower(): entry
            for entry in prep_matched_entries
        }
        for noun_token in grand_children:
            if _to_str(noun_token.get("pos_tag", "")).upper() != "NOUN":
                continue

            noun_lemma = _to_str(noun_token.get("lemma_word", "")).lower()
            matched_entry = noun_entry_map.get(noun_lemma)
            if matched_entry is None:
                continue

            return _build_candidate(
                sentence_id=sentence_id,
                fvg_entry_id=_to_str(matched_entry.get("id")),
                verb_token=verb_token,
                noun_token=noun_token,
                prep_token=prep_token,
            )

    return None
