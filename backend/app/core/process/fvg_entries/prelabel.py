from collections.abc import Iterable, Sequence


class FvgPrelabel:
    def __init__(self) -> None:
        self._nlp = self._load_nlp()

    def _load_nlp(self):
        try:
            import spacy  # type: ignore
        except Exception:
            return None

        for model_name in ("de_core_news_md", "de_core_news_sm"):
            try:
                return spacy.load(model_name)
            except Exception:
                continue

        try:
            return spacy.blank("de")
        except Exception:
            return None

    def label(self, rows: object) -> list[dict[str, str]]:
        normalized_rows = self._normalize_rows(rows)
        labeled_rows: list[dict[str, str]] = []

        for row in normalized_rows:
            prep, noun = self.find_prep_noun(row["phrase"])
            structure_type = self.find_structure_type(prep)
            semantic_type = self.find_semantic_type(
                phrase=row["phrase"],
                prep=prep,
                noun=noun,
            )

            labeled_rows.append(
                {
                    "verb": row["verb"],
                    "phrase": row["phrase"],
                    "noun": noun,
                    "prep": prep,
                    "structure_type": structure_type,
                    "semantic_type": semantic_type,
                }
            )

        return labeled_rows

    def _normalize_rows(self, rows: object) -> list[dict[str, str]]:
        if hasattr(rows, "iterrows"):
            normalized: list[dict[str, str]] = []
            for _, row in rows.iterrows():
                verb = str(row.iloc[0]).strip()
                phrase = str(row.iloc[1]).strip()
                if not verb or not phrase:
                    continue
                normalized.append({"verb": verb, "phrase": phrase})
            return normalized

        normalized = []
        if isinstance(rows, Iterable):
            for row in rows:
                if isinstance(row, dict):
                    verb = str(row.get("verb", "")).strip()
                    phrase = str(row.get("phrase", "")).strip()
                elif isinstance(row, Sequence) and len(row) >= 2:
                    verb = str(row[0]).strip()
                    phrase = str(row[1]).strip()
                else:
                    continue

                if not verb or not phrase:
                    continue

                normalized.append({"verb": verb, "phrase": phrase})

        return normalized

    def find_prep_noun(self, phrase: str) -> tuple[str, str]:
        if self._nlp is None:
            return self._fallback_prep_noun(phrase)

        doc = self._nlp(phrase)

        prep = ""
        noun = ""
        for token in doc:
            if not prep and token.pos_ == "ADP":
                prep = token.text
                continue

            if token.pos_ in {"NOUN", "PROPN", "PRON"}:
                noun = token.text
                if prep:
                    break

        if not noun:
            noun = self._fallback_noun_from_phrase(phrase)

        return prep, noun

    def find_structure_type(self, prep: str) -> str:
        return "prep" if prep.strip() else "akku"

    def find_semantic_type(self, *, phrase: str, prep: str, noun: str) -> str:
        normalized_prep = prep.strip().lower()
        if normalized_prep in {
            "in",
            "an",
            "auf",
            "unter",
            "ueber",
            "vor",
            "hinter",
            "zwischen",
            "bei",
            "zu",
            "nach",
        }:
            return "locative"
        if normalized_prep in {"mit", "ohne", "fuer", "gegen", "aus"}:
            return "relation"

        if noun and phrase:
            return "general"
        return "unknown"

    def _fallback_prep_noun(self, phrase: str) -> tuple[str, str]:
        tokens = [part for part in phrase.strip().split() if part]
        if not tokens:
            return "", ""

        preps = {
            "in",
            "an",
            "auf",
            "unter",
            "ueber",
            "vor",
            "hinter",
            "zwischen",
            "bei",
            "zu",
            "nach",
            "mit",
            "ohne",
            "fuer",
            "gegen",
            "aus",
        }

        prep = ""
        noun = ""
        for index, token in enumerate(tokens):
            normalized = token.lower()
            if not prep and normalized in preps:
                prep = token
                if index + 1 < len(tokens):
                    noun = tokens[index + 1]
                break

        if not noun:
            noun = tokens[-1]

        return prep, noun

    def _fallback_noun_from_phrase(self, phrase: str) -> str:
        tokens = [part for part in phrase.strip().split() if part]
        return tokens[-1] if tokens else ""
