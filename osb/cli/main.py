from __future__ import annotations

import argparse

from osb import __version__
from osb import profiling
from osb.config import params, settings
from osb.config.attributes import ATTRIBUTE_CATALOG


def _cmd_info(args: argparse.Namespace) -> int:
    print(f"Online Support Bubble (OSB) v{__version__}")
    print(f"  curve             : {params.CURVE_NAME} ({params.SECURITY_LEVEL_BITS}-bit security)")
    print(f"  scalar field bits : {params.SCALAR_FIELD_ORDER.bit_length()}")
    print(f"  transport         : {settings.TRANSPORT}")
    print(f"  attributes ({len(ATTRIBUTE_CATALOG)})   : {', '.join(ATTRIBUTE_CATALOG)}")
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    from osb.cli.demo import run_demo

    return profiling.run_and_log(run_demo, "demo")


def _cmd_shell(args: argparse.Namespace) -> int:
    from osb.cli.shell import run_shell

    return profiling.run_and_log(run_shell, "shell")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="osb",
        description="Online Support Bubble - privacy-preserving support groups (CLI).",
    )
    parser.add_argument("--version", action="version", version=f"osb {__version__}")
    sub = parser.add_subparsers(dest="_command", metavar="<command>")

    sub.add_parser("info", help="show build / curve / config info").set_defaults(func=_cmd_info)
    sub.add_parser(
        "demo", help="run a scripted end-to-end scenario (writes time_log / space_log)"
    ).set_defaults(func=_cmd_demo)
    sub.add_parser(
        "shell", help="interactive shell to drive the protocol (writes time_log / space_log)"
    ).set_defaults(func=_cmd_shell)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "_command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
