import argparse

from app.services.document.add_document_service import add_document
from app.services.document.remove_document_service import remove_document_with_text_cleanup


def register(subparsers) -> None:
    document_parser = subparsers.add_parser("document", help="Document use-case scripts")
    document_subparsers = document_parser.add_subparsers(
        dest="document_command",
        required=True,
    )

    add_parser = document_subparsers.add_parser("add", help="Add a document")
    add_parser.add_argument("file_path", help="Document file path")
    add_parser.set_defaults(handler=_handle_add_document)

    remove_parser = document_subparsers.add_parser("remove", help="Remove a document")
    remove_parser.add_argument("document_id", help="Document id")
    remove_parser.set_defaults(handler=_handle_remove_document)


def _handle_add_document(args: argparse.Namespace) -> dict:
    return add_document(args.file_path)


def _handle_remove_document(args: argparse.Namespace) -> dict:
    return remove_document_with_text_cleanup(args.document_id)
