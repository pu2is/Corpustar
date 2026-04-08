from functools import lru_cache

LemmaTokenRow = dict[str, int | str]


@lru_cache(maxsize=1)
def _get_tag_map() -> dict[str, str]:
    """Return a mapping of STTS fine POS tag -> UD coarse POS tag from spaCy's German tag_map."""
    try:
        from spacy.lang.de.tag_map import TAG_MAP  # type: ignore
        return {stts: attrs.get("pos", "") for stts, attrs in TAG_MAP.items()}
    except Exception:
        return {}


def edit_lemma(
    old_row: LemmaTokenRow,
    new_lemma_word: str,
    new_pos_tag: str,
) -> LemmaTokenRow:
    """
    Return a corrected LemmaTokenRow based on user-supplied lemma_word and pos_tag.

    Rules:
    - lemma_word and pos_tag are always overwritten with the user-supplied values.
    - fine_pos_tag is validated against the spaCy TAG_MAP:
        if the existing fine_pos_tag maps to the new pos_tag -> keep it.
        otherwise -> clear it.
    - morph is bound to fine_pos_tag: cleared when fine_pos_tag is cleared.
    - dependency_relationship is always kept (syntactic role is context-assigned, not POS-driven).
    """
    tag_map = _get_tag_map()
    existing_fine_pos = str(old_row.get("fine_pos_tag", ""))

    mapped_ud_pos = tag_map.get(existing_fine_pos, "")
    fine_pos_valid = bool(existing_fine_pos) and mapped_ud_pos == new_pos_tag

    return {
        **old_row,
        "lemma_word": new_lemma_word,
        "pos_tag": new_pos_tag,
        "fine_pos_tag": existing_fine_pos if fine_pos_valid else "",
        "morph": str(old_row.get("morph", "")) if fine_pos_valid else "",
    }
