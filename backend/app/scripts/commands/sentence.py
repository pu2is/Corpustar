import argparse

from app.services.sentence.sentence_edit_service import clip_sentence, merge_sentences


def register(subparsers) -> None:
    sentence_parser = subparsers.add_parser("sentence", help="Sentence edit use-case scripts")
    sentence_subparsers = sentence_parser.add_subparsers(
        dest="sentence_command",
        required=True,
    )

    merge_parser = sentence_subparsers.add_parser("merge", help="Merge sentences")
    merge_parser.add_argument("sentence_ids", nargs="+", help="Sentence ids")
    merge_parser.set_defaults(handler=_handle_merge_sentences)

    clip_parser = sentence_subparsers.add_parser("clip", help="Clip a sentence")
    clip_parser.add_argument("sentence_id", help="Sentence id")
    clip_parser.add_argument("split_offset", type=int, help="Split offset")
    clip_parser.set_defaults(handler=_handle_clip_sentence)


def _handle_merge_sentences(args: argparse.Namespace) -> dict:
    return merge_sentences(args.sentence_ids)


def _handle_clip_sentence(args: argparse.Namespace) -> dict:
    return clip_sentence(
        sentence_id=args.sentence_id,
        split_offset=args.split_offset,
    )
