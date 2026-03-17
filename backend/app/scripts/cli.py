import argparse
import json
import sys

from app.scripts.commands.document import register as register_document_commands
from app.scripts.commands.process import register as register_process_commands
from app.scripts.commands.sentence import register as register_sentence_commands


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="corpustar-script")
    subparsers = parser.add_subparsers(
        dest="domain",
        required=True,
    )
    register_document_commands(subparsers)
    register_process_commands(subparsers)
    register_sentence_commands(subparsers)
    return parser


def _print_result(result: object) -> None:
    if result is None:
        return
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2

    try:
        result = handler(args)
        _print_result(result)
        return 0
    except Exception as error:
        payload = {
            "error": str(error),
            "type": type(error).__name__,
        }
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
