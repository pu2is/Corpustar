from collections.abc import Mapping


LemmaTokenRow = Mapping[str, int | str]
LemmaTokenItem = dict[str, int | str | list]


def _parse_morph(morph: str) -> list[dict[str, str]]:
    if not morph:
        return []
    result = []
    for part in morph.split("|"):
        eq = part.find("=")
        if eq == -1:
            result.append({"key": part, "value": ""})
        else:
            result.append({"key": part[:eq], "value": part[eq + 1:]})
    return result


def build_lemma_token_item(
    *,
    token_id: str,
    version_id: str,
    sentence_id: str,
    source_word: str,
    lemma_word: str,
    word_index: int,
    head_index: int,
    pos_tag: str,
    fine_pos_tag: str,
    morph: str,
    dependency_relationship: str,
) -> LemmaTokenItem:
    return {
        "id": token_id,
        "version_id": version_id,
        "sentence_id": sentence_id,
        "source_word": source_word,
        "lemma_word": lemma_word,
        "word_index": word_index,
        "head_index": head_index,
        "pos_tag": pos_tag,
        "fine_pos_tag": fine_pos_tag,
        "morph": _parse_morph(morph),
        "dependency_relationship": dependency_relationship,
    }


def build_lemma_token_item_from_row(row: LemmaTokenRow) -> LemmaTokenItem:
    return build_lemma_token_item(
        token_id=str(row["id"]),
        version_id=str(row["version_id"]),
        sentence_id=str(row["sentence_id"]),
        source_word=str(row["source_word"]),
        lemma_word=str(row["lemma_word"]),
        word_index=int(row["word_index"]),
        head_index=int(row["head_index"]),
        pos_tag=str(row["pos_tag"]),
        fine_pos_tag=str(row["fine_pos_tag"]),
        morph=str(row["morph"]),
        dependency_relationship=str(row["dependency_relationship"]),
    )
