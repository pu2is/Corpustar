from pathlib import Path


def save_text_content(doc_id: str, text: str) -> str:
    text_dir = Path(__file__).resolve().parents[2] / "storage" / "texts"
    text_dir.mkdir(parents=True, exist_ok=True)

    text_path = text_dir / f"{doc_id}.txt"
    text_path.write_text(text, encoding="utf-8")

    return str(text_path.resolve())
