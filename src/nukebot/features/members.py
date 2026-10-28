"""Member nuke and management features."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import discord

from nukebot.core.rate_limit import RateLimiter
from nukebot.core.templates import render_template
from nukebot.features.common import Context, Result


def _members(ctx: Context, include_bots: bool = False) -> list[Any]:
    members = list(ctx.guild.members)
    if not include_bots:
        members = [m for m in members if not m.bot]
    return members


async def mass_ban(ctx: Context, members: list[Any], reason: str = "Nuked", delete_message_days: int = 0) -> Result:
    result = Result(action="mass_ban")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("ban", "member", len(members))
        result.success = len(members)
        return result
    for member in members:
        try:
            await ctx.rate_limiter.run(
                lambda member=member: ctx.guild.ban(member, reason=reason, delete_message_days=delete_message_days),
                "ban",
            )
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"ban {getattr(member, 'id', member)}: {exc}")
    return result


async def mass_kick(ctx: Context, members: list[Any], reason: str = "Nuked") -> Result:
    result = Result(action="mass_kick")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("kick", "member", len(members))
        result.success = len(members)
        return result
    for member in members:
        try:
            await ctx.rate_limiter.run(lambda member=member: member.kick(reason=reason), "kick")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"kick {getattr(member, 'id', member)}: {exc}")
    return result


async def mass_timeout(ctx: Context, members: list[Any], seconds: int, reason: str = "Nuked") -> Result:
    result = Result(action="mass_timeout")
    until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    if ctx.dry_run.enabled:
        ctx.dry_run.record("timeout", "member", len(members))
        result.success = len(members)
        return result
    for member in members:
        try:
            await ctx.rate_limiter.run(lambda member=member: member.timeout(until, reason=reason), "timeout")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"timeout {getattr(member, 'id', member)}: {exc}")
    return result


async def mass_unban(ctx: Context, user_ids: list[int], reason: str = "Unbanned") -> Result:
    result = Result(action="mass_unban")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("unban", "user", len(user_ids))
        result.success = len(user_ids)
        return result
    for user_id in user_ids:
        try:
            user = await ctx.client.fetch_user(user_id)
            await ctx.rate_limiter.run(lambda user=user: ctx.guild.unban(user, reason=reason), "unban")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"unban {user_id}: {exc}")
    return result


async def mass_nickname(ctx: Context, members: list[Any], template: str) -> Result:
    result = Result(action="mass_nickname")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("nickname", "member", len(members))
        result.success = len(members)
        return result
    for index, member in enumerate(members, start=1):
        name = render_template(template, index, {"name": getattr(member, "name", ""), "guild": ctx.guild.name})
        try:
            await ctx.rate_limiter.run(lambda member=member, name=name: member.edit(nick=name), "nickname")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"nickname {getattr(member, 'id', member)}: {exc}")
    return result


async def mass_move_to_voice(ctx: Context, members: list[Any], channel: Any) -> Result:
    result = Result(action="mass_move_voice")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("move_voice", "member", len(members))
        result.success = len(members)
        return result
    for member in members:
        try:
            await ctx.rate_limiter.run(lambda member=member: member.move_to(channel), "move_voice")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"move {getattr(member, 'id', member)}: {exc}")
    return result


async def mass_voice_state(ctx: Context, members: list[Any], mute: bool | None = None, deafen: bool | None = None) -> Result:
    result = Result(action="mass_voice_state")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("voice_state", "member", len(members))
        result.success = len(members)
        return result
    for member in members:
        try:
            kwargs = {}
            if mute is not None:
                kwargs["mute"] = mute
            if deafen is not None:
                kwargs["deafen"] = deafen
            await ctx.rate_limiter.run(lambda member=member, kwargs=kwargs: member.edit(**kwargs), "voice_state")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"voice_state {getattr(member, 'id', member)}: {exc}")
    return result


async def mass_dm(ctx: Context, members: list[Any], content: str, count: int = 1) -> Result:
    result = Result(action="mass_dm")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("mass_dm", "member", len(members) * count)
        result.success = len(members) * count
        return result
    for _ in range(count):
        for member in members:
            try:
                await ctx.rate_limiter.run(lambda member=member: member.send(content), "mass_dm")
                result.success += 1
            except Exception as exc:  # noqa: BLE001
                result.add_error(f"dm {getattr(member, 'id', member)}: {exc}")
    return result


async def scrape_members(ctx: Context, include_bots: bool = False) -> list[int]:
    members = _members(ctx, include_bots=include_bots)
    return [m.id for m in members]


async def prune_members(ctx: Context, days: int = 30) -> Result:
    result = Result(action="prune_members")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("prune_members", "member", 0)
        result.success = 0
        return result
    try:
        pruned = await ctx.rate_limiter.run(lambda: ctx.guild.prune_members(days=days, compute_prune_count=True), "prune_members")
        result.success = int(pruned or 0)
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"prune: {exc}")
    return result


async def join_invite(ctx: Context, invite_code: str) -> Result:
    result = Result(action="join_invite")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("join_invite", invite_code, 1)
        result.success = 1
        return result
    try:
        invite = await ctx.client.fetch_invite(invite_code)
        await ctx.rate_limiter.run(lambda: invite.accept(), "join_invite")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"join_invite {invite_code}: {exc}")
    return result


async def leave_guild(ctx: Context) -> Result:
    result = Result(action="leave_guild")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("leave_guild", ctx.guild.name, 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: ctx.guild.leave(), "leave_guild")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"leave_guild: {exc}")
    return result
