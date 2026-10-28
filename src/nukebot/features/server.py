"""Server metadata nuke and management features."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import discord

from nukebot.features.common import Context, Result


async def rename_server(ctx: Context, name: str) -> Result:
    result = Result(action="rename_server")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("rename_server", name, 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: ctx.guild.edit(name=name), "rename_server")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"rename_server: {exc}")
    return result


async def set_icon(ctx: Context, path_or_url: str) -> Result:
    result = Result(action="set_icon")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("set_icon", path_or_url, 1)
        result.success = 1
        return result
    try:
        data = None
        p = Path(path_or_url)
        if p.exists():
            data = p.read_bytes()
        else:
            import aiohttp

            async with ctx.client.http_session if hasattr(ctx.client, "http_session") else aiohttp.ClientSession() as session:
                async with session.get(path_or_url) as resp:
                    data = await resp.read()
        await ctx.rate_limiter.run(lambda: ctx.guild.edit(icon=data), "set_icon")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"set_icon: {exc}")
    return result


async def set_banner(ctx: Context, path_or_url: str) -> Result:
    result = Result(action="set_banner")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("set_banner", path_or_url, 1)
        result.success = 1
        return result
    try:
        data = None
        p = Path(path_or_url)
        if p.exists():
            data = p.read_bytes()
        else:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(path_or_url) as resp:
                    data = await resp.read()
        await ctx.rate_limiter.run(lambda: ctx.guild.edit(banner=data), "set_banner")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"set_banner: {exc}")
    return result


async def set_verification_level(ctx: Context, level: Any) -> Result:
    result = Result(action="set_verification_level")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("set_verification_level", str(level), 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: ctx.guild.edit(verification_level=level), "set_verification_level")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"set_verification_level: {exc}")
    return result


async def set_notifications(ctx: Context, level: Any) -> Result:
    result = Result(action="set_notifications")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("set_notifications", str(level), 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: ctx.guild.edit(default_notifications=level), "set_notifications")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"set_notifications: {exc}")
    return result


async def set_content_filter(ctx: Context, level: Any) -> Result:
    result = Result(action="set_content_filter")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("set_content_filter", str(level), 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: ctx.guild.edit(explicit_content_filter=level), "set_content_filter")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"set_content_filter: {exc}")
    return result


async def set_system_channel(ctx: Context, channel: Any) -> Result:
    result = Result(action="set_system_channel")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("set_system_channel", str(getattr(channel, "id", channel)), 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: ctx.guild.edit(system_channel=channel), "set_system_channel")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"set_system_channel: {exc}")
    return result


async def set_afk(ctx: Context, channel: Any, timeout: int) -> Result:
    result = Result(action="set_afk")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("set_afk", str(getattr(channel, "id", channel)), 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: ctx.guild.edit(afk_channel=channel, afk_timeout=timeout), "set_afk")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"set_afk: {exc}")
    return result
