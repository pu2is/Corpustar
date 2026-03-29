from app.infrastructure.repositories.documents import read_all_documents


def list_documents() -> list[dict[str, int | str]]:
    return read_all_documents()
