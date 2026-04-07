from collections.abc import Mapping
from functools import lru_cache
from uuid import uuid4

SentenceRow = Mapping[str, int | str]
LemmaTokenRow = dict[str, int | str]

def _normalize_morph(morph: object) -> str:
    text = str(morph)
    return text if text and text != "_" else ""

@lru_cache(maxsize=1)
def _load_spacy_model():
    try:
        import spacy  # type: ignore
    except Exception as error:
        raise RuntimeError("spaCy is required for lemmatize process") from error

    for model_name in ("de_core_news_md", "de_core_news_sm"):
        try:
            return spacy.load(model_name)
        except Exception:
            continue

    raise RuntimeError(
        "spaCy German model is required. Install de_core_news_md (preferred) or de_core_news_sm."
    )


def lemmatize_sentence_to_tokens(sentence_row: SentenceRow, *, version_id: str) -> list[LemmaTokenRow]:
    nlp = _load_spacy_model()

    sentence_id = str(sentence_row["id"])
    corrected_text = str(sentence_row["corrected_text"])
    doc = nlp(corrected_text)

    # 1. remove spaces, assign stable original indices
    non_space_tokens = [token for token in doc if not token.is_space]
    token_to_orig_index = {token: index for index, token in enumerate(non_space_tokens)}

    # 2. preprocess separable verbs (svp):
    #    merge the svp prefix into the root verb's lemma (e.g., zeigt + an -> anzeigen)
    #    the svp token itself is still written to DB with its own original word_index
    verb_lemmas: dict = {}
    for token in non_space_tokens:
        if token.dep_ == "svp":
            head = token.head
            prefix = token.lemma_ if token.lemma_ else token.text
            base_verb = verb_lemmas.get(head, head.lemma_ if head.lemma_ else head.text)
            verb_lemmas[head] = (prefix + base_verb).lower()

    # 3. write ALL non-space tokens — word_index equals original position, no gaps
    #    head_index uses the direct spaCy dependency head (no traversal needed)
    result: list[LemmaTokenRow] = []
    for token in non_space_tokens:
        orig_word_index = token_to_orig_index[token]
        head_index = token_to_orig_index.get(token.head, orig_word_index)
        final_lemma = verb_lemmas.get(token, token.lemma_ if token.lemma_ else token.text)

        result.append(
            {
                "id": str(uuid4()),
                "version_id": version_id,
                "sentence_id": sentence_id,
                "source_word": token.text,
                "lemma_word": final_lemma,
                "word_index": orig_word_index,
                "head_index": int(head_index),
                "pos_tag": token.pos_ or "",
                "fine_pos_tag": token.tag_ or "",
                "morph": _normalize_morph(token.morph),
                "dependency_relationship": token.dep_ or "",
            }
        )

    return result