import argparse
import sys

from slowcrunch import version_string
from slowcrunch.tui.repl import run_repl


def _build_argument_parser():
    parser = argparse.ArgumentParser(prog="slowcrunch")
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="show the installed slowcrunch version and exit",
    )
    parser.add_argument(
        "session_name",
        nargs="?",
        help="start or reopen a named session",
    )
    return parser


def main(argv=None):
    args = _build_argument_parser().parse_args([] if argv is None else argv)
    if args.version:
        print(version_string())
        return 0

    run_repl(session_name=args.session_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
