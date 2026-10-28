"""Entry point for the Discord nuker."""

from __future__ import annotations

import argparse
import asyncio

from nukebot.cli.commands import build_parser, run_commands
from nukebot.cli.menu import run_interactive
from nukebot.storage.config import Config
from nukebot.storage.logging import setup_logging
from nukebot.storage.secrets import load_dotenv


import sys

def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    parser = build_parser()
    args = parser.parse_args(argv)
    load_dotenv()
    config = Config.load(args.config)
    if args.mode:
        config.mode = args.mode
    setup_logging(config.log_level)

    if args.command is None:
        try:
            return asyncio.run(run_interactive(config))
        except KeyboardInterrupt:
            print("Interrupted.")
            return 130
        except Exception as exc:  # noqa: BLE001
            print(f"Error: {exc}")
            return 1
    return asyncio.run(run_commands(args))


if __name__ == "__main__":
    raise SystemExit(main())
