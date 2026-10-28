"""Argparse subcommands for automation."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from nukebot.core.client import create_client, close_client
from nukebot.core.intents import make_intents
from nukebot.storage.config import Config
from nukebot.storage.secrets import get_token, load_dotenv
from nukebot.features.common import Context
from nukebot.features.raid import token_check
from nukebot.features.utility import guild_info, backup_guild
from nukebot.features.raid import token_check
from nukebot.core.rate_limit import RateLimiter
from nukebot.core.dryrun import DryRunContext
from nukebot.ui.console import render_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nukebot")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--mode", choices=["bot", "selfbot", "user"])
    parser.add_argument("--profile", default="default")
    parser.add_argument("--token")
    parser.add_argument("--guild", type=int)
    parser.add_argument("--dry-run", action="store_true")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("token-check")
    sub.add_parser("guild-info")
    sub.add_parser("backup")
    restore = sub.add_parser("restore")
    restore.add_argument("backup_path")
    run = sub.add_parser("run")
    run.add_argument("action")
    run.add_argument("--channel-id", type=int)
    run.add_argument("--role-id", type=int)
    run.add_argument("--count", type=int, default=10)
    run.add_argument("--name", default="nuke-{i}")
    return parser


async def _bootstrap(args):
    load_dotenv()
    config = Config.load(args.config)
    mode = args.mode or config.mode
    token = get_token(mode, args.profile, args.token)
    if not token:
        raise RuntimeError("No token found. Set BOT_TOKEN/USER_TOKEN or use --token.")
    intents = make_intents(mode)
    client = await create_client(mode, token, intents, proxy=config.proxy)
    mode = client.mode
    await client.wait_until_ready()
    guild = client.get_guild(args.guild) if args.guild else None
    if args.guild and guild is None:
        guild = await client.fetch_guild(args.guild)
    rate_limiter = RateLimiter(max_concurrency=config.max_workers_for_mode(mode))
    dry_run = DryRunContext(enabled=args.dry_run or config.default_dry_run)
    ctx = Context(client=client, guild=guild, rate_limiter=rate_limiter, dry_run=dry_run, mode=mode, logger=None, config=config)
    return client, ctx


async def run_commands(args) -> int:
    if args.command == "token-check":
        load_dotenv()
        config = Config.load(args.config)
        mode = args.mode or config.mode
        token = get_token(mode, args.profile, args.token)
        if not token:
            raise RuntimeError("No token found.")
        client = await create_client(mode, token, make_intents(mode), proxy=config.proxy)
        mode = client.mode
        await client.wait_until_ready()
        info = await token_check(client)
        print(info)
        await close_client(client)
        return 0

    client, ctx = await _bootstrap(args)
    try:
        if args.command == "guild-info":
            print(await guild_info(ctx))
        elif args.command == "backup":
            if ctx.guild is None:
                raise RuntimeError("--guild is required")
            result = await backup_guild(ctx)
            render_result(result)
            print(result.details)
        elif args.command == "restore":
            if ctx.guild is None:
                raise RuntimeError("--guild is required")
            result = await restore_guild(ctx, args.backup_path)
            render_result(result)
        elif args.command == "run":
            if ctx.guild is None:
                raise RuntimeError("--guild is required")
            await _run_action(ctx, args)
        else:
            print("No command provided. Use --help.")
    finally:
        await close_client(client)
    return 0


async def _run_action(ctx, args) -> None:
    from nukebot.features import channels, roles, messages, members, server, webhooks, emojis, threads, integrations

    action = args.action
    if action == "spam-channel":
        channel = ctx.guild.get_channel(args.channel_id) if args.channel_id else None
        result = await messages.spam_messages(ctx, channel, args.name, args.count)
        render_result(result)
    elif action == "nuke-channel" and args.channel_id:
        channel = ctx.guild.get_channel(args.channel_id)
        result = await channels.nuke_channel(ctx, channel)
        render_result(result)
    else:
        print(f"Unsupported or incomplete run action: {action}")


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(run_commands(args))
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")
        return 1
