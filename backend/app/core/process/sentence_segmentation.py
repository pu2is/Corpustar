SENTENCE_END_CHARS = frozenset({".", "!", "?"})
TRAILING_CLOSER_CHARS = frozenset({'"', "'", ")", "]", "}"})


def _skip_leading_whitespace(text: str, start_index: int) -> int:
    index = max(start_index, 0)
    text_length = len(text)
    while index < text_length and text[index].isspace():
        index += 1
    return index


def segment_sentences(full_text: str) -> list[dict[str, int]]:
    if full_text == "":
        return []

    text_length = len(full_text)
    sentence_start = _skip_leading_whitespace(full_text, 0)
    if sentence_start >= text_length:
        return []

    spans: list[dict[str, int]] = []
    index = sentence_start

    while index < text_length:
        char = full_text[index]
        if char in SENTENCE_END_CHARS:
            sentence_end = index + 1

            while sentence_end < text_length and full_text[sentence_end] in SENTENCE_END_CHARS:
                sentence_end += 1

            while sentence_end < text_length and full_text[sentence_end] in TRAILING_CLOSER_CHARS:
                sentence_end += 1

            if full_text[sentence_start:sentence_end].strip():
                spans.append(
                    {
                        "start_offset": sentence_start,
                        "end_offset": sentence_end,
                    }
                )

            sentence_start = _skip_leading_whitespace(full_text, sentence_end)
            index = sentence_start
            continue

        index += 1

    if sentence_start < text_length:
        sentence_end = text_length
        while sentence_end > sentence_start and full_text[sentence_end - 1].isspace():
            sentence_end -= 1

        if sentence_end > sentence_start and full_text[sentence_start:sentence_end].strip():
            spans.append(
                {
                    "start_offset": sentence_start,
                    "end_offset": sentence_end,
                }
            )

    return spans
