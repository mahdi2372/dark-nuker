"""Raid helper features."""

from __future__ import annotations

from typing import Any

import discord

from nukebot.features.common import Context, Result


async def token_check(client: Any) -> dict[str, Any]:
    try:
        user = client.user
        if user is None:
            await client.wait_until_ready()
            user = client.user
        guilds = [g.name for g in client.guilds]
        return {"valid": True, "user": str(user), "id": user.id, "guilds": guilds}
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "error": str(exc)}


async def guild_scrape(ctx: Context) -> dict[str, Any]:
    return {
        "guild_id": ctx.guild.id,
        "name": ctx.guild.name,
        "owner_id": ctx.guild.owner_id,
        "member_count": ctx.guild.member_count,
        "channels": len(ctx.guild.channels),
        "roles": len(ctx.guild.roles),
        "emojis": len(ctx.guild.emojis),
        "stickers": len(ctx.guild.stickers),
        "boost_level": ctx.guild.premium_tier,
        "created_at": ctx.guild.created_at.isoformat() if ctx.guild.created_at else None,
    }


async def permission_audit(ctx: Context) -> dict[str, bool]:
    from nukebot.core.permissions import permission_summary

    return permission_summary(ctx.client, ctx.guild)


async def leave_all_guilds(ctx: Context) -> Result:
    result = Result(action="leave_all_guilds")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("leave_guild", "all", len(ctx.client.guilds))
        result.success = len(ctx.client.guilds)
        return result
    for guild in list(ctx.client.guilds):
        try:
            await ctx.rate_limiter.run(lambda guild=guild: guild.leave(), "leave_guild")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"leave {guild.id}: {exc}")
    return result
