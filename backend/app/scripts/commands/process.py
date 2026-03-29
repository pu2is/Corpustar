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
    segment_parser.add_argument(
        "--preview-length",
        type=int,
        default=0,
        help="Preview sentence count",
    )
    segment_parser.set_defaults(handler=_handle_segment_sentences)

    page_parser = process_subparsers.add_parser(
        "sentence-page",
        help="Get sentence page by segmentation cursor",
    )
    page_parser.add_argument("doc_id", help="Document id")
    page_parser.add_argument("segmentation_id", help="Segmentation id")
    page_parser.add_argument(
        "--split-offset",
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
    return segment_document_sentences(args.doc_id, args.preview_length)


def _handle_sentence_page(args: argparse.Namespace) -> dict:
    return get_sentence_cursor_page(
        doc_id=args.doc_id,
        segmentation_id=args.segmentation_id,
        split_offset=args.split_offset,
        limit=args.limit,
    )
