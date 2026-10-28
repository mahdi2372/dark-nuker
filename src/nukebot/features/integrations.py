"""Integration management features."""

from __future__ import annotations

import discord

from nukebot.features.common import Context, Result


async def list_bots(ctx: Context) -> list[Any]:
    return [m for m in ctx.guild.members if m.bot]


async def remove_bots(ctx: Context, bots: list[Any] | None = None) -> Result:
    result = Result(action="remove_bots")
    targets = bots or await list_bots(ctx)
    if ctx.dry_run.enabled:
        ctx.dry_run.record("remove_bot", "bot", len(targets))
        result.success = len(targets)
        return result
    for bot in targets:
        try:
            await ctx.rate_limiter.run(lambda bot=bot: bot.kick(reason="Nuked integrations"), "remove_bot")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"remove_bot {getattr(bot, 'id', bot)}: {exc}")
    return result
