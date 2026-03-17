from app.infrastructure.repositories.document_repository import get_all_documents


def list_documents() -> list[dict]:
    return get_all_documents()
