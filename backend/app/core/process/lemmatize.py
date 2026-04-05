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

    # 1. remove space get index
    non_space_tokens = [token for token in doc if not token.is_space]
    token_to_orig_index = {token: index for index, token in enumerate(non_space_tokens)}

    # 2. preprocess separable verbs (svp)
    verb_lemmas = {}
    svp_tokens = set()
    for token in non_space_tokens:
        if token.dep_ == "svp":
            head = token.head
            svp_tokens.add(token)
            
            # combine prefix and base verb (e.g., ab + hängen -> abhängen)
            prefix = token.lemma_ if token.lemma_ else token.text
            base_verb = verb_lemmas.get(head, head.lemma_ if head.lemma_ else head.text)
            verb_lemmas[head] = (prefix + base_verb).lower()

    # 3. define skeleton, filter tokens (put into set for O(1) lookup)
    # note: "davon" is usually tagged as ADV in spaCy, so we need to keep ADV and PRON
    KEEP_POS = {"NOUN", "PROPN", "VERB", "ADP", "PRON", "ADV"}
    
    kept_tokens = set()
    for token in non_space_tokens:
        if token in svp_tokens: 
            continue # discard svp (already merged into Root)
        if token.pos_ not in KEEP_POS:
            continue # discard auxiliary verbs (AUX), determiners (DET), punctuation (PUNCT), etc.
        kept_tokens.add(token)

    # 4. generate final result and fix head_index
    result: list[LemmaTokenRow] = []
    
    # iterate over non_space_tokens to maintain order, but only process kept tokens
    for token in non_space_tokens:
        if token not in kept_tokens:
            continue
            
        # strictly use original index
        orig_word_index = token_to_orig_index[token]
        
        current_head = token.head
        while current_head not in kept_tokens and current_head != current_head.head:
            current_head = current_head.head
            
        # determine head_index:
        # if tracing reaches Root and Root is also filtered out (rare), use itself as head
        if current_head not in kept_tokens:
            head_index = orig_word_index
        else:
            head_index = token_to_orig_index[current_head]

        # determine the final lemma_word (if it's a verb with a prefix, use the combined word)
        final_lemma = verb_lemmas.get(token, token.lemma_ if token.lemma_ else token.text)

        result.append(
            {
                "id": str(uuid4()),
                "version_id": version_id,
                "sentence_id": sentence_id,
                "source_word": token.text,
                "lemma_word": final_lemma,
                "word_index": orig_word_index,        # <--- strictly use original index
                "head_index": int(head_index),
                "pos_tag": token.pos_ or "",
                "fine_pos_tag": token.tag_ or "",
                "morph": _normalize_morph(token.morph),
                "dependency_relationship": token.dep_ or "",
            }
        )

    return result