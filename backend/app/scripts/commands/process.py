import argparse
from app.services.process.sentence_segmentation import segment_document_sentences
from app.services.sentence.pagination import get_sentence_cursor_page


def register(subparsers) -> None:
    process_parser = subparsers.add_parser("process", help="Process use-case scripts")
    process_subparsers = process_parser.add_subparsers(
        dest="process_command",
        required=True,
    )

    segment_parser = process_subparsers.add_parser(
        "segment-sentences",
        help="Run sentence segmentation for a document",
    )
    segment_parser.add_argument("doc_id", help="Document id")
    segment_parser.set_defaults(handler=_handle_segment_sentences)

    latest_parser = process_subparsers.add_parser(
        "latest-segmentation",
        help="Get latest sentence segmentation result",
    )
    latest_parser.add_argument("doc_id", help="Document id")

    page_parser = process_subparsers.add_parser(
        "sentence-page",
        help="Get sentence page by processing cursor",
    )
    page_parser.add_argument("doc_id", help="Document id")
    page_parser.add_argument("processing_id", help="Processing id")
    page_parser.add_argument(
        "--after-start-offset",
        type=int,
        default=None,
        help="Cursor start offset",
    )
    page_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Page size",
    )
    page_parser.set_defaults(handler=_handle_sentence_page)


def _handle_segment_sentences(args: argparse.Namespace) -> dict:
    return segment_document_sentences(args.doc_id)


def _handle_sentence_page(args: argparse.Namespace) -> dict:
    return get_sentence_cursor_page(
        doc_id=args.doc_id,
        processing_id=args.processing_id,
        after_start_offset=args.after_start_offset,
        limit=args.limit,
    )
