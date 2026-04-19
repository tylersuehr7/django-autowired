"""Command-line interface for django-autowired."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from django_autowired.inspect import (
    render_json,
    render_mermaid,
    render_table,
    render_tree,
    report,
    scan,
)

_RENDERERS = {
    "table": render_table,
    "tree": render_tree,
    "json": render_json,
    "mermaid": render_mermaid,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m django_autowired",
        description="django-autowired command-line tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = subparsers.add_parser(
        "inspect",
        help="Scan packages and print a report of registered @injectable bindings.",
    )
    inspect_cmd.add_argument(
        "packages",
        nargs="+",
        help="Dotted package paths to scan (e.g. myapp.services myapp.adapters).",
    )
    inspect_cmd.add_argument(
        "--format",
        "-f",
        choices=sorted(_RENDERERS),
        default="table",
        help="Output format (default: table).",
    )
    inspect_cmd.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="SEGMENT",
        help=(
            "Additional module name segments to skip (repeatable). "
            "Merged with built-ins (migrations, tests, test, conftest, factories, fixtures)."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        exclude = set(args.exclude) if args.exclude else None
        scan(*args.packages, exclude_patterns=exclude)
        rows = report()
        print(_RENDERERS[args.format](rows))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
